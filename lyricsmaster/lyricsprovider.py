# -*- coding: utf-8 -*-

"""Lyrics Providers."""
from .lyricsmaster import Song, Album, Discography

import requests
from bs4 import BeautifulSoup

import gevent.monkey
gevent.monkey.patch_socket()
from gevent.pool import Pool

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
        else:
            self.session = self.get_tor_session(ip, socksport)

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
            controller.signal(Signal.NEWNYM)

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
        for elmt in albums:
            ## Renewal of tor session conflicts with gevent
            ## When executing self.renew_tor_circuit(), the following error occurs
            ## gevent.hub.LoopExit: ('This operation would block forever', <Hub at 0x1c677090e88 select pending=0 ref=0>)
            ## Circuit change is disabled for now
            # if self.controlport:
            #     self.renew_tor_circuit(self.controlport, self.password)
            #     self.session = self.get_tor_session(self.ip, self.socksport)
            print('Downloading {0}'.format(elmt.text))
            album_title = elmt.text
            song_links = self.get_songs(elmt)
            pool = Pool(25) # Sets the worker pool for async requests
            results = [pool.spawn(self.create_song, *(link, author, album_title)) for link in song_links]
            pool.join() # Gathers results from the pool
            songs = [song.value for song in results]
            album = Album(album_title, author, songs)
            album_objects.append(album)
        discography = Discography(author, album_objects)
        return discography


if __name__ == "__main__":
    pass
