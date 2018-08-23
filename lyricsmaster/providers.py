# -*- coding: utf-8 -*-

"""Main module.

This module defines the Api interface for the various Lyrics providers.
All lyrics providers inherit from the base class LyricsProvider.

"""

# We use abstract methods to ensure that all future classes inheriting from LyricsProvider will
# implement the required methods in order to have a nice and consistent API.
from abc import ABCMeta, abstractmethod

import re
import urllib3
import certifi
from bs4 import BeautifulSoup

# We use gevent in order to make asynchronous http requests while downloading lyrics.
# It is also used to patch the socket module to use SOCKS5 instead to interface with the Tor controller.
import gevent.monkey
from gevent.pool import Pool

# Python 2.7 compatibility
# Works for Python 2 and 3
try:
    from importlib import reload
except ImportError:
    try:
        from imp import reload
    except:
        pass

# Importing the app models and utilities
from .models import Song, Album, Discography
from .utils import normalize

class LyricsProvider:
    """
    This is the base class for all Lyrics Providers. If you wish to subclass this class, you must implement all
    the methods defined in this class to be compatible with the LyricsMaster API.
    Requests to fetch songs are executed asynchronously for better performance.
    Tor anonymisation is provided if tor is installed on the system and a TorController is passed at instance creation.

    :param tor_controller: TorController Object.

    """
    __metaclass__ = ABCMeta
    name = ''

    def __init__(self, tor_controller=None):
        if not self.__socket_is_patched():
            gevent.monkey.patch_socket()
        self.tor_controller = tor_controller
        if not self.tor_controller:
            user_agent = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'}
            self.session = urllib3.PoolManager(maxsize=10, cert_reqs='CERT_REQUIRED', ca_certs=certifi.where(),
                                               headers=user_agent)
        else:
            self.session = self.tor_controller.get_tor_session()
        self.__tor_status__()

    def __repr__(self):
        return '{0}.{1}({2})'.format(__name__, self.__class__.__name__, self.tor_controller.__repr__())

    def __tor_status__(self):
        """
        Informs the user of the Tor status.

        """
        if not self.tor_controller:
            print('Anonymous requests disabled. The connexion will not be anonymous.')
        elif self.tor_controller and not self.tor_controller.controlport:
            print('Anonymous requests enabled. The Tor circuit will change according to the Tor network defaults.')
        else:
            print('Anonymous requests enabled. The Tor circuit will change for each album.')

    def __socket_is_patched(self):
        """
        Checks if the socket is patched or not.

        :return: bool.
        """
        return gevent.monkey.is_module_patched('socket')

    @abstractmethod
    def _has_lyrics(self, page):
        """
        Must be implemented by children classes conforming to the LyricsMaster API.

        Checks if the lyrics provider has the lyrics for the song or not.

        :param page:
        :return: bool.
        """
        pass

    @abstractmethod
    def _has_artist(self, page):
        """
        Must be implemented by children classes conforming to the LyricsMaster API.

        Check if the artist is in the lyrics provider's database.

        :param page:
        :return: bool.
        """
        pass

    @abstractmethod
    def _make_artist_url(self, artist):
        """
        Must be implemented by children classes conforming to the LyricsMaster API.

        Builds an url for the artist page of the lyrics provider.

        :param artist:
        :return: string or None.
        """
        pass

    @abstractmethod
    def _clean_string(self, text):
        """
        Must be implemented by children classes conforming to the LyricsMaster API.

        Formats the text to conform to the lyrics provider formatting.

        :param text:
        :return: string or None.
        """
        pass

    def get_page(self, url):
        """
        Fetches the supplied url and returns a request object.

        :param url: string.
        :return: urllib3.response.HTTPResponse Object or None.
        """
        if not self.__socket_is_patched():
            gevent.monkey.patch_socket()
        try:
            req = self.session.request('GET', url)
        except Exception as e:
            print(e)
            req = None
            print('Unable to download url ' + url)
        return req

    def get_lyrics(self, artist, album=None, song=None):
        """
        This is the main method of this class.
        Connects to the Lyrics Provider and downloads lyrics for all the albums of the supplied artist and songs.
        Returns a Discography Object or None if the artist was not found on the Lyrics Provider.

        :param artist: string
            Artist name.
        :return: models.Discography object or None.
        """

        raw_html = self.get_artist_page(artist)
        if not raw_html:
            print('{0} was not found on {1}'.format(artist, self.name))
            return None
        albums = self.get_albums(raw_html)
        if album:
            # If user supplied a specific album
            albums = [elmt for elmt in albums if album.lower() in self.get_album_infos(elmt)[0].lower()]
        album_objects = []
        for elmt in albums:
            try:
                album_title, release_date = self.get_album_infos(elmt)
            except ValueError as e:
                pass
                print('Error {0} while downloading {1}'.format(e, album_title))
                continue
            song_links = self.get_songs(elmt)
            if song:
                # If user supplied a specific song
                song_links = [link for link in song_links if song.lower() in link.text.lower()]
            if self.tor_controller and self.tor_controller.controlport:
                # Renew Tor circuit before starting downloads.
                self.tor_controller.renew_tor_circuit()
                self.session = self.tor_controller.get_tor_session()
            print('Downloading {0}'.format(album_title))
            pool = Pool(25)  # Sets the worker pool for async requests. 25 is a nice value to not annoy site owners ;)
            results = [pool.spawn(self.create_song, *(link, artist, album_title)) for link in song_links]
            pool.join()  # Gathers results from the pool
            songs = [song.value for song in results]
            album_obj = Album(album_title, artist, songs, release_date)
            album_objects.append(album_obj)
            print('{0} succesfully downloaded'.format(album_title))
        discography = Discography(artist, album_objects)
        return discography

    def get_artist_page(self, artist):
        """
        Fetches the web page for the supplied artist.

        :param artist: string.
            Artist name.
        :return: string or None.
            Artist's raw html page. None if the artist page was not found.
        """
        artist = self._clean_string(artist)
        url = self._make_artist_url(artist)
        if not url:
            return None
        raw_html = self.get_page(url).data
        artist_page = BeautifulSoup(raw_html, 'lxml')
        if not self._has_artist(artist_page):
            return None
        return raw_html

    def get_lyrics_page(self, url):
        """
        Fetches the web page containing the lyrics at the supplied url.

        :param url: string.
            Lyrics url.
        :return: string or None.
            Lyrics's raw html page. None if the lyrics page was not found.
        """
        raw_html = self.get_page(url).data
        lyrics_page = BeautifulSoup(raw_html, 'lxml')
        if not self._has_lyrics(lyrics_page):
            return None
        return raw_html

    @abstractmethod
    def get_albums(self, raw_artist_page):
        """
        Must be implemented by children classes conforming to the LyricsMaster API.

        Fetches the albums section in the supplied html page.

        :param raw_artist_page: Artist's raw html page.
        :return: list.
            List of BeautifulSoup objects.
        """
        pass

    @abstractmethod
    def get_album_infos(self, tag):
        """
        Must be implemented by children classes conforming to the LyricsMaster API.

        Extracts the Album informations from the tag

        :param tag: BeautifulSoup object.
        :return: tuple(string, string).
            Album title and release date.
        """
        pass

    @abstractmethod
    def get_songs(self, album):
        """
        Must be implemented by children classes conforming to the LyricsMaster API.

        Fetches the links to the songs of the supplied album.

        :param album: BeautifulSoup object.
        :return: List of BeautifulSoup Link objects.
        """
        pass

    @abstractmethod
    def create_song(self, link, artist, album_title):
        """
        Must be implemented by children classes conforming to the LyricsMaster API.

        Creates a Song object.

        :param link: BeautifulSoup Link object.
        :param artist: string.
        :param album_title: string.
        :return: models.Song object or None.
        """
        pass

    @abstractmethod
    def extract_lyrics(self, song):
        """
        Must be implemented by children classes conforming to the LyricsMaster API.

        Extracts the lyrics from the lyrics page of the supplied song.

        :param lyrics_page: BeautifulSoup Object.
            BeautifulSoup lyrics page.
        :return: string or None.
            Formatted lyrics.
        """
        pass

    @abstractmethod
    def extract_writers(self, lyrics_page):
        """
        Must be implemented by children classes conforming to the LyricsMaster API.

        Extracts the writers from the lyrics page of the supplied song.

        :param lyrics_page: BeautifulSoup Object.
            BeautifulSoup lyrics page.
        :return: string or None.
            Song writers.
        """
        pass


class LyricWiki(LyricsProvider):
    """
    Class interfacing with http://lyrics.wikia.com .
    This class is used to retrieve lyrics from LyricWiki.

    """
    base_url = 'http://lyrics.wikia.com'
    name = 'LyricWiki'

    def _has_lyrics(self, lyrics_page):
        """
        Checks if the lyrics provider has the lyrics for the song or not.

        :param lyrics_page:
        :return: bool.
        """
        return not lyrics_page.find("div", {'class': 'noarticletext'})

    _has_artist = _has_lyrics

    def _make_artist_url(self, artist):
        """
        Builds an url for the artist page of the lyrics provider.

        :param artist:
        :return: string.
        """
        url = self.base_url + '/wiki/' + artist
        return url

    def get_album_page(self, artist, album):
        """
        Fetches the album page for the supplied artist and album.

        :param artist: string.
            Artist name.
        :param album: string.
            Album title.
        :return: string or None.
            Album's raw html page. None if the album page was not found.
        """
        artist = self._clean_string(artist)
        album = self._clean_string(album)
        url = self.base_url + '/wiki/' + artist + ':' + album
        raw_html = self.get_page(url).data
        album_page = BeautifulSoup(raw_html, 'lxml')
        if album_page.find("div", {'class': 'noarticletext'}):
            return None
        return raw_html

    def get_albums(self, raw_artist_page):
        """
        Fetches the albums section in the supplied html page.

        :param raw_artist_page: Artist's raw html page.
        :return: list.
            List of BeautifulSoup objects.
        """
        artist_page = BeautifulSoup(raw_artist_page, 'lxml')
        albums = [tag for tag in artist_page.find_all("span", {'class': 'mw-headline'}) if
                  tag.attrs['id'] not in ('Additional_information', 'External_links')]
        return albums

    def get_album_infos(self, tag):
        """
        Extracts the Album informations from the tag

        :param tag: BeautifulSoup object.
        :return: tuple(string, string).
            Album title and release date.
        """
        try:
            i = tag.text.index(' (')
            release_date = re.findall(r'\(([^()]+)\)', tag.text)[0]
        except ValueError:
            i = -1
            release_date = 'Unknown'
        album_title = tag.text[:i]

        return album_title, release_date

    def get_songs(self, album):
        """
        Fetches the links to the songs of the supplied album.

        :param album: BeautifulSoup object.
        :return: List of BeautifulSoup Link objects.
        """
        parent_node = album.parent
        while parent_node.name != 'ol':
            parent_node = parent_node.next_sibling
        song_links = [elmt.find('a') for elmt in parent_node.find_all('li')]
        return song_links

    def create_song(self, link, artist, album_title):
        """
        Creates a Song object.

        :param link: BeautifulSoup Link object.
        :param artist: string.
        :param album_title: string.
        :return: models.Song object or None.
        """
        if not link.attrs['href'].startswith(self.base_url):
            song_url = self.base_url + link.attrs['href']
        else:
            song_url = link.attrs['href']
        song_title = link.attrs['title']
        song_title = song_title[song_title.index(':') + 1:]
        if '(page does not exist' in song_title:
            return None
        raw_lyrics_page = self.get_lyrics_page(song_url)
        if not raw_lyrics_page:
            return None
        lyrics_page = BeautifulSoup(raw_lyrics_page, 'lxml')
        lyrics = self.extract_lyrics(lyrics_page)
        writers = self.extract_writers(lyrics_page)
        song = Song(song_title, album_title, artist, lyrics, writers)
        return song

    def extract_lyrics(self, lyrics_page):
        """
        Extracts the lyrics from the lyrics page of the supplied song.

        :param lyrics_page: BeautifulSoup Object.
            BeautifulSoup lyrics page.
        :return: string or None.
            Formatted lyrics.
        """
        lyric_box = lyrics_page.find("div", {'class': 'lyricbox'})
        lyrics = '\n'.join(lyric_box.strings)
        return lyrics

    def extract_writers(self, lyrics_page):
        """
        Extracts the writers from the lyrics page of the supplied song.

        :param lyrics_page: BeautifulSoup Object.
            BeautifulSoup lyrics page.
        :return: string or None.
            Song writers.
        """
        writers_box = lyrics_page.find("table", {'class': 'song-credit-box'})
        if writers_box:
            writers = writers_box.find_all('p')[-1].text.strip()
        else:
            writers = None
        return writers

    def _clean_string(self, text):
        """
        Cleans the supplied string and formats it to use in a url.

        :param text: string.
            Text to be cleaned.
        :return: string.
            Cleaned text.
        """
        for elmt in [('#', 'Number_'), ('[', '('), (']', ')'), ('{', '('), ('}', ')'), (' ', '_')]:
            text = text.replace(*elmt)
        return text


class AzLyrics(LyricsProvider):
    """
    Class interfacing with https://azlyrics.com .
    This class is used to retrieve lyrics from AzLyrics.

    """
    base_url = 'https://www.azlyrics.com'
    search_url = 'https://search.azlyrics.com/search.php?q='
    name = 'AzLyrics'

    def _has_lyrics(self, lyrics_page):
        """
        Checks if the lyrics provider has the lyrics for the song or not.

        :param lyrics_page:
        :return: bool.
        """
        if lyrics_page.find("div", {'class': 'lyricsh'}):
            return True
        else:
            return False

    def _has_artist(self, page):
        """
        Check if the artist is in the lyrics provider's database.

        :param lyrics_page:
        :return: bool.
        """
        if page.find("div", {'id': 'listAlbum'}):
            return True
        else:
            return False

    def _has_artist_result(self, page):
        """
        Checks if the lyrics provider has the lyrics for the song or not.

        :param lyrics_page:
        :return: bool.
        """
        artist_result = page.find("div", {'class': 'panel-heading'})
        if artist_result.find('b').text == 'Artist results:':
            return True
        else:
            return False

    def _make_artist_url(self, artist):
        """
        Builds an url for the artist page of the lyrics provider.

        :param artist:
        :return: string.
        """
        return self.search(artist)

    def search(self, artist):
        """
        Searches for the artist in the supplier's database.

        :param artist: Artist's name.
        :return: url or None.
            Url to the artist's page if found. None if not Found.
        """
        artist = artist.replace(' ', '+')
        if artist.lower().startswith('the'):
            artist = artist[4:]
        url = self.search_url + artist
        search_results = self.get_page(url).data
        results_page = BeautifulSoup(search_results, 'lxml')
        if not self._has_artist_result(results_page):
            return None
        target_node = results_page.find("div", {'class': 'panel-heading'}).find_next_sibling("table")
        artist_url = target_node.find('a').attrs['href']
        if not artist_url:
            return None
        if not artist_url.startswith(self.base_url):
            artist_url = self.base_url + artist_url
        return artist_url

    def get_albums(self, raw_artist_page):
        """
        Fetches the albums section in the supplied html page.

        :param raw_artist_page: Artist's raw html page.
        :return: list.
            List of BeautifulSoup objects.
        """
        artist_page = BeautifulSoup(raw_artist_page, 'lxml')
        albums = [tag for tag in artist_page.find_all("div", {'id': 'listAlbum'})]
        return albums

    def get_album_infos(self, tag):
        """
        Extracts the Album informations from the tag

        :param tag: BeautifulSoup object.
        :return: tuple(string, string).
            Album title and release date.
        """
        album_infos = tag.find("div", {'class': 'album'}).text
        album_title = re.findall(r'"([^"]*)"', album_infos)[0]
        try:
            release_date = re.findall(r'\(([^()]+)\)', tag.text)[0]
        except ValueError:
            release_date = 'Unknown'
        return album_title, release_date

    def get_songs(self, album):
        """
        Fetches the links to the songs of the supplied album.

        :param album: BeautifulSoup object.
        :return: List of BeautifulSoup Link objects.
        """
        song_links = album.find_all('a')
        song_links = [song for song in song_links if 'href' in song.attrs]
        return song_links

    def create_song(self, link, artist, album_title):
        """
        Creates a Song object.

        :param link: BeautifulSoup Link object.
        :param artist: string.
        :param album_title: string.
        :return: models.Song object or None.
        """
        song_title = link.text
        raw_lyrics_page = self.get_lyrics_page(self.base_url + link.attrs['href'].replace('..', ''))
        if not raw_lyrics_page:
            return None
        lyrics_page = BeautifulSoup(raw_lyrics_page, 'lxml')
        lyrics = self.extract_lyrics(lyrics_page)
        writers = self.extract_writers(lyrics_page)
        song = Song(song_title, album_title, artist, lyrics, writers)
        return song

    def extract_lyrics(self, lyrics_page):
        """
        Extracts the lyrics from the lyrics page of the supplied song.

        :param lyrics_page: BeautifulSoup Object.
            BeautifulSoup lyrics page.
        :return: string.
            Formatted lyrics.
        """
        lyric_box = lyrics_page.find("div", {"class": None, "id": None})
        lyrics = ''.join(lyric_box.strings)
        return lyrics

    def extract_writers(self, lyrics_page):
        """
        Extracts the writers from the lyrics page of the supplied song.

        :param lyrics_page: BeautifulSoup Object.
            BeautifulSoup lyrics page.
        :return: string or None.
            Song writers or None.
        """
        writers_box = lyrics_page.find("div", {'class': 'smt'})
        if writers_box:
            writers = writers_box.text.strip()
        else:
            writers = None
        return writers

    def _clean_string(self, text):
        """
        Cleans the supplied string and formats it to use in a url.

        :param text: string.
            Text to be cleaned.
        :return: string.
            Cleaned text.
        """
        return text


class Genius(LyricsProvider):
    """
    Class interfacing with https://genius.com .
    This class is used to retrieve lyrics from Genius.

    """
    base_url = 'https://genius.com'
    search_url = base_url + '/search?q='
    name = 'Genius'

    def _has_lyrics(self, page):
        """
        Checks if the lyrics provider has the lyrics for the song or not.

        :param lyrics_page:
        :return: bool.
        """
        if page.find("div", {'class': 'song_body-lyrics'}):
            return True
        else:
            return False

    def _has_artist(self, page):
        """
        Check if the artist is in the lyrics provider's database.

        :param lyrics_page:
        :return: bool.
        """
        if not page.find("div", {'class': 'render_404'}):
            return True
        else:
            return False

    def _make_artist_url(self, artist):
        """
        Builds an url for the artist page of the lyrics provider.

        :param artist:
        :return: string.
        """
        url = self.base_url + '/artists/' + artist
        return url

    def get_albums(self, raw_artist_page):
        """
        Fetches the albums section in the supplied html page.

        :param raw_artist_page: Artist's raw html page.
        :return: list.
            List of BeautifulSoup objects.
        """
        artist_page = BeautifulSoup(raw_artist_page, 'lxml')
        albums_link = artist_page.find("a", {'class': 'full_width_button'})
        albums_link = albums_link.attrs['href'].replace('songs?', 'albums?')
        albums_page = BeautifulSoup(self.get_page(self.base_url + albums_link).data, 'lxml')
        albums = [tag for tag in albums_page.find_all("a", {'class': 'album_link'})]
        return albums

    def get_album_infos(self, tag):
        """
        Extracts the Album informations from the tag

        :param tag: BeautifulSoup object.
        :return: tuple(string, string).
            Album title and release date.
        """
        album_title = tag.text
        album_page = BeautifulSoup(self.get_page(self.base_url + tag.attrs['href']).data, 'lxml')
        info_box = album_page.find("div", {'class': 'header_with_cover_art-primary_info'})
        metadata = [elmt for elmt in info_box.find_all("div", {'class': 'metadata_unit'}) if elmt.text.startswith('Released')]
        try:
            release_date = metadata[0].text
        except IndexError:
            release_date = 'Unknown'
        except ValueError:
            release_date = 'Unknown'
        return album_title, release_date

    def get_songs(self, album):
        """
        Fetches the links to the songs of the supplied album.

        :param album: BeautifulSoup object.
        :return: List of BeautifulSoup Link objects.
        """
        album_page = BeautifulSoup(self.get_page(self.base_url + album.attrs['href']).data, 'lxml')
        song_links = album_page.find_all("div", {'class': 'chart_row chart_row--light_border chart_row--full_bleed_left chart_row--align_baseline chart_row--no_hover'})
        song_links = [song.find('a') for song in song_links]
        return song_links

    def create_song(self, link, artist, album_title):
        """
        Creates a Song object.

        :param link: BeautifulSoup Link object.
        :param artist: string.
        :param album_title: string.
        :return: models.Song object or None.
        """
        if not link.attrs['href'].startswith(self.base_url):
            song_url = self.base_url + link.attrs['href']
        else:
            song_url = link.attrs['href']
        song_title = link.text.strip('\n').split('\n')[0].lstrip()
        raw_lyrics_page = self.get_lyrics_page(song_url)
        if not raw_lyrics_page:
            return None
        lyrics_page = BeautifulSoup(raw_lyrics_page, 'lxml')
        lyrics = self.extract_lyrics(lyrics_page)
        writers = self.extract_writers(lyrics_page)
        song = Song(song_title, album_title, artist, lyrics, writers)
        return song

    def extract_lyrics(self, lyrics_page):
        """
        Extracts the lyrics from the lyrics page of the supplied song.

        :param lyrics_page: BeautifulSoup Object.
            BeautifulSoup lyrics page.
        :return: string.
            Formatted lyrics.
        """
        lyric_box = lyrics_page.find("div", {"class": 'lyrics'})
        lyrics = ''.join(lyric_box.strings)
        return lyrics

    def extract_writers(self, lyrics_page):
        """
        Extracts the writers from the lyrics page of the supplied song.

        :param lyrics_page: BeautifulSoup Object.
            BeautifulSoup lyrics page.
        :return: string.
            Song writers or None.
        """
        writers_box = [elmt for elmt in lyrics_page.find_all("span", {'class': 'metadata_unit-label'}) if elmt.text == "Written By"]
        if writers_box:
            target_node = writers_box[0].find_next_sibling("span", {'class': 'metadata_unit-info'})
            writers = target_node.text.strip()
        else:
            writers = None
        return writers

    def _clean_string(self, text):
        """
        Cleans the supplied string and formats it to use in a url.

        :param text: string.
            Text to be cleaned.
        :return: string.
            Cleaned text.
        """
        text = normalize(text).lower().capitalize()
        return text


class Lyrics007(LyricsProvider):
    """
    Class interfacing with https://www.lyrics007.com .
    This class is used to retrieve lyrics from Lyrics007.

    """
    base_url = 'https://www.lyrics007.com'
    search_url = base_url + '/search.php?category=artist&q='
    name = 'Lyrics007'

    def _has_lyrics(self, page):
        """
        Checks if the lyrics provider has the lyrics for the song or not.

        :param lyrics_page:
        :return: bool.
        """
        if page.find("div", {'class': 'lyrics'}):
            return True
        else:
            return False

    def _has_artist(self, page):
        """
        Check if the artist is in the lyrics provider's database.

        :param lyrics_page:
        :return: bool.
        """
        if page.find("ul", {'class': 'song_title'}):
            return True
        else:
            return False

    def _has_artist_result(self, page):
        """
        Check if the artist is in the lyrics provider's database.

        :param lyrics_page:
        :return: bool.
        """
        artist_link = page.find("div", {'id': 'search_result'}).find('a')
        if artist_link:
            return True
        else:
            return False

    def _make_artist_url(self, artist):
        """
        Builds an url for the artist page of the lyrics provider.

        :param artist:
        :return: string.
        """
        return self.search(artist)

    def search(self, artist):
        """
        Searches for the artist in the supplier's database.

        :param raw_artist_page: Artist's raw html page.
        :return: string or None.
            Artist's url page.
        """
        artist = "".join([c if (c.isalnum() or c == '.') else "+" for c in artist])
        url = self.search_url + artist
        search_results = self.get_page(url).data
        results_page = BeautifulSoup(search_results, 'lxml')
        if not self._has_artist_result(results_page):
            return None
        artist_url = results_page.find("div", {'id': 'search_result'}).find('a').attrs['href']
        if not artist_url:
            return None
        if not artist_url.startswith(self.base_url):
            artist_url = self.base_url + artist_url
        return artist_url

    def get_albums(self, raw_artist_page):
        """
        Fetches the albums section in the supplied html page.

        :param raw_artist_page: Artist's raw html page.
        :return: list.
            List of BeautifulSoup objects.
        """
        artist_page = BeautifulSoup(raw_artist_page, 'lxml')
        albums = [tag for tag in artist_page.find_all('li') if tag.find('b')]
        return albums

    def get_album_infos(self, tag):
        """
        Extracts the Album informations from the tag

        :param tag: BeautifulSoup object.
        :return: tuple(string, string).
            Album title and release date.
        """
        # TODO: Verify order of release_date, album_title = tag.text.split(': ')
        release_date, album_title = tag.text.split(': ')
        return album_title, release_date

    def get_songs(self, album):
        """
        Fetches the links to the songs of the supplied album.

        :param album: BeautifulSoup object.
        :return: List of BeautifulSoup Link objects.
        """
        target_node = album.find_next_sibling("ul")
        song_links = [elmt.find('a') for elmt in target_node.find_all('li') if elmt.find('a')]
        return song_links

    def create_song(self, link, artist, album_title):
        """
        Creates a Song object.

        :param link: BeautifulSoup Link object.
        :param artist: string.
        :param album_title: string.
        :return: models.Song object or None.
        """
        if not link.attrs['href'].startswith(self.base_url):
            song_url = self.base_url + link.attrs['href']
        else:
            song_url = link.attrs['href']
        song_title = link.text
        raw_lyrics_page = self.get_lyrics_page(song_url)
        if not raw_lyrics_page:
            return None
        lyrics_page = BeautifulSoup(raw_lyrics_page, 'lxml')
        lyrics = self.extract_lyrics(lyrics_page)
        writers = self.extract_writers(lyrics_page)
        song = Song(song_title, album_title, artist, lyrics, writers)
        return song

    def extract_lyrics(self, lyrics_page):
        """
        Extracts the lyrics from the lyrics page of the supplied song.

        :param lyrics_page: BeautifulSoup Object.
            BeautifulSoup lyrics page.
        :return: string.
            Formatted lyrics.
        """
        lyric_box = lyrics_page.find("div", {'class': 'lyrics'})
        lyrics = '\n'.join(lyric_box.strings)
        return lyrics

    def extract_writers(self, lyrics_page):
        """
        Extracts the writers from the lyrics page of the supplied song.

        :param lyrics_page: BeautifulSoup Object.
            BeautifulSoup lyrics page.
        :return: string.
            Song writers or None.
        """
        writers_box = [elmt for elmt in lyrics_page.strings if
                       elmt.lower().startswith('writers:') or elmt.lower().startswith('writer:')]
        if writers_box:
            writers = writers_box[0].strip()
        else:
            writers = None
        return writers

    def _clean_string(self, text):
        """
        Cleans the supplied string and formats it to use in a url.

        :param text: string.
            Text to be cleaned.
        :return: string.
            Cleaned text.
        """
        return text


class MusixMatch(LyricsProvider):
    """
    Class interfacing with https://www.musixmatch.com .
    This class is used to retrieve lyrics from MusixMatch.

    """
    base_url = 'https://www.musixmatch.com'
    search_url = base_url + '/search/{0}/artists'
    name = 'MusixMatch'

    def _has_lyrics(self, page):
        """
        Checks if the lyrics provider has the lyrics for the song or not.

        :param lyrics_page:
        :return: bool.
        """
        if page.find("p", {'class': 'mxm-lyrics__content '}):
            return True
        else:
            return False

    def _has_artist(self, page):
        """
        Check if the artist is in the lyrics provider's database.

        :param lyrics_page:
        :return: bool.
        """
        if page.find("div", {'class': 'artist-page main-wrapper'}):
            return True
        else:
            return False

    def _make_artist_url(self, artist):
        """
        Builds an url for the artist page of the lyrics provider.

        :param artist:
        :return: string.
        """
        return self.base_url + '/artist/' + artist

    def get_albums(self, raw_artist_page):
        """
        Fetches the albums section in the supplied html page.

        :param raw_artist_page: Artist's raw html page.
        :return: list.
            List of BeautifulSoup objects.
        """
        artist_page = BeautifulSoup(raw_artist_page, 'lxml')
        albums_link = artist_page.find("li", {'id': 'albums'})
        albums_link = albums_link.find('a').attrs['href']
        albums_page = BeautifulSoup(self.get_page(self.base_url + albums_link).data, 'lxml')
        albums = [tag for tag in albums_page.find_all("div", {'class': 'media-card-text'})]
        return albums

    def get_album_infos(self, tag):
        """
        Extracts the Album informations from the tag

        :param tag: BeautifulSoup object.
        :return: tuple(string, string).
            Album title and release date.
        """
        album_title = tag.find('h2').text
        try:
            release_date = tag.find('h3').text
        except AttributeError:
            release_date = 'Unknown'
        return album_title, release_date

    def get_songs(self, album):
        """
        Fetches the links to the songs of the supplied album.

        :param album: BeautifulSoup object.
        :return: List of BeautifulSoup Link objects.
        """
        album_page = BeautifulSoup(self.get_page(self.base_url + album.find('a').attrs['href']).data, 'lxml')
        album_div = album_page.find("div", {'class': 'mxm-album__tracks mxm-collection-container'})
        song_links = album_div.find_all("li", {'class': re.compile("^mui-collection__item")})
        song_links = [song.find('a') for song in song_links]
        return song_links

    def create_song(self, link, artist, album_title):
        """
        Creates a Song object.

        :param link: BeautifulSoup Link object.
        :param artist: string.
        :param album_title: string.
        :return: models.Song object or None.
        """
        if not link.attrs['href'].startswith(self.base_url):
            song_url = self.base_url + link.attrs['href']
        else:
            song_url = link.attrs['href']
        song_title = link.text
        raw_lyrics_page = self.get_lyrics_page(song_url)
        if not raw_lyrics_page:
            return None
        lyrics_page = BeautifulSoup(raw_lyrics_page, 'lxml')
        lyrics = self.extract_lyrics(lyrics_page)
        writers = self.extract_writers(lyrics_page)
        song = Song(song_title, album_title, artist, lyrics, writers)
        return song

    def extract_lyrics(self, lyrics_page):
        """
        Extracts the lyrics from the lyrics page of the supplied song.

        :param lyrics_page: BeautifulSoup Object.
            BeautifulSoup lyrics page.
        :return: string.
            Formatted lyrics.
        """
        lyric_box = lyrics_page.find("p", {'class': re.compile("^mxm-lyrics__content")})
        lyrics = '\n'.join(lyric_box.strings)
        return lyrics

    def extract_writers(self, lyrics_page):
        """
        Extracts the writers from the lyrics page of the supplied song.

        :param lyrics_page: BeautifulSoup Object.
            BeautifulSoup lyrics page.
        :return: string.
            Song writers or None.
        """
        writers_box = lyrics_page.find("p", {'class': re.compile("^mxm-lyrics__copyright")})
        if writers_box:
            writers = writers_box.text.strip()
        else:
            writers = None
        return writers

    def _clean_string(self, text):
        """
        Cleans the supplied string and formats it to use in a url.

        :param text: string.
            Text to be cleaned.
        :return: string.
            Cleaned text.
        """
        text = text.replace(' ', '-').replace('.', '-')
        if text[-1] == '-':
            text = text[:-1]
        return text

if __name__ == "__main__":
    pass
