# -*- coding: utf-8 -*-

"""Lyrics Providers."""
from .lyricsmaster import Song, Album, Discography

import requests
from bs4 import BeautifulSoup

import gevent.monkey
from gevent.pool import Pool

import socket

try:
    from importlib import reload
except ImportError:
    try:
        from imp import reload
    except:
        pass

from stem import Signal
from stem.control import Controller


class LyricsProvider:
    def __init__(self, tor=False, ip='127.0.0.1', socksport=9050, controlport=None, password=''):
        """

        :param tor: boolean
        :param ip: string
        :param socksport: integer
        :param controlport: integer
        :param password: string
        """
        self.socksport = socksport
        self.ip = ip
        self.controlport = controlport
        self.password = password
        if not tor:
            self.session = requests.session()
            print('Asynchronous requests enabled. The connexion is not anonymous.')
        else:
            self.session = self.get_tor_session(ip, socksport)
            print('Anonymous requests enabled.')
            if not controlport:
                print('Asynchronous requests enabled but the tor circuit will not change for each album.')
            else:
                print('Asynchronous requests disabled to allow the creation of new tor circuits for each album')

    def get_page(self, url):
        """

        :param url: string
        :return: requests.request Object
        """
        try:
            req = self.session.get(url)
        except:
            req = None
            print('Unable to download url ' + url)
        return req

    def get_tor_session(self, ip, port):
        """

        :param ip: integer
        :param port: integer
        :return: requests.session Object
        """
        session = requests.session()
        session.proxies = {'http': 'socks5://{0}:{1}'.format(ip, port),
                           'https': 'socks5://{0}:{1}'.format(ip, port)}
        return session

    def renew_tor_circuit(self, port, password):
        """

        :param port: integer
        :param password: string
        """
        with Controller.from_port(port=port) as controller:
            controller.authenticate(password=password)
            if controller.is_newnym_available():  # true if tor would currently accept a NEWNYM signal
                controller.signal(Signal.NEWNYM)
                print('New Tor circuit created')
                return True
            else:
                delay = controller.get_newnym_wait()
                print('Dealy to create new Tor circuit: {0}s'.format(delay))
                return False

    def get_lyrics(self, author):
        """

        :param author:
        """
        pass

    def get_artist_page(self, author):
        """

        :param author:
        """
        pass

    def get_album_page(self, author, album):
        """

        :param author:
        :param album:
        """
        pass

    def get_lyrics_page(self, url):
        """

        :param url:
        """
        pass

    def extract_lyrics(self, song):
        """

        :param song:
        """
        pass


class LyricWiki(LyricsProvider):
    base_url = 'http://lyrics.wikia.com'

    def clean_string(self, text):
        """

        :param text: string
        :return: string
        """
        for elmt in [('#', 'Number_'), ('[', '('), (']', ')'), ('{', '('), ('}', ')'), (' ', '_')]:
            text = text.replace(*elmt)
        return text

    def get_artist_page(self, author):
        """

        :param author: string
        :return: BeautifulSoup Object
        """
        author = self.clean_string(author)
        url = self.base_url + '/wiki/' + author
        artist_page = BeautifulSoup(self.get_page(url).text, 'lxml')
        if artist_page.find("div", {'class': 'noarticletext'}):
            return None
        return artist_page

    def get_album_page(self, author, album):
        """

        :param author: string
        :param album: string
        :return: BeautifulSoup Object or None
        """
        author = self.clean_string(author)
        album = self.clean_string(album)
        url = self.base_url + '/wiki/' + author + ':' + album
        album_page = BeautifulSoup(self.get_page(url).text, 'lxml')
        if album_page.find("div", {'class': 'noarticletext'}):
            return None
        return album_page

    def get_lyrics_page(self, url):
        """

        :param url: string
        :return: BeautifulSoup Object or None.
        """
        lyrics_page = BeautifulSoup(self.get_page(url).text, 'lxml')
        if lyrics_page.find("div", {'class': 'noarticletext'}):
            return None
        return lyrics_page

    def get_songs(self, album):
        """

        :param album: BeautifulSoup Object
        :return: List of BeautifulSoup Link Objects
        """
        parent_node = album.parent
        while parent_node.name != 'ol':
            parent_node = parent_node.next_sibling
        song_links = parent_node.find_all('li')
        return song_links

    def extract_lyrics(self, song):
        """

        :param song: BeautifulSoup Object
        :return: string
        """
        lyric_box = song.find("div", {'class': 'lyricbox'})
        lyrics = lyric_box.text
        return lyrics

    def create_song(self, link, author, album_title):
        """

        :param link: BeautifulSoup Link Object
        :param author: string
        :param album_title: string
        :return: lyricsmaster.Song Object or None.
        """
        link = link.find('a')
        song_title = link.attrs['title']
        song_title = song_title[song_title.index(':') + 1:]
        if '(page does not exist' in song_title:
            return None
        lyrics_page = self.get_lyrics_page(self.base_url + link.attrs['href'])
        if not lyrics_page:
            return None
        lyrics = self.extract_lyrics(lyrics_page)
        song = Song(song_title, album_title, author, lyrics)
        return song

    def get_lyrics(self, author):
        """

        :param author: string
        :return: lyricsmaster.Discography Object or None.
        """
        artist_page = self.get_artist_page(author)
        if not artist_page:
            return None
        albums = [tag for tag in artist_page.find_all("span", {'class': 'mw-headline'}) if
                  tag.attrs['id'] not in ('Additional_information', 'External_links')]
        album_objects = []
        if not self.controlport: # cycle circuits
            gevent.monkey.patch_socket()
        for elmt in albums:
            album_title = elmt.text
            song_links = self.get_songs(elmt)
            print('Downloading {0}'.format(elmt.text))
            if self.controlport:
                self.renew_tor_circuit(self.controlport, self.password)
                self.session = self.get_tor_session(self.ip, self.socksport)
                songs = [self.create_song(link, author, album_title) for link in song_links]
            else:
                pool = Pool(25)  # Sets the worker pool for async requests
                results = [pool.spawn(self.create_song, *(link, author, album_title)) for link in song_links]
                pool.join()  # Gathers results from the pool
                songs = [song.value for song in results]
            album = Album(album_title, author, songs)
            album_objects.append(album)
        if not self.controlport:
            reload(socket)
        discography = Discography(author, album_objects)
        return discography


if __name__ == "__main__":
    pass
