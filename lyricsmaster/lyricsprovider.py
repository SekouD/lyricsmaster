# -*- coding: utf-8 -*-

"""Lyrics Providers."""
from .lyricsmaster import Song, Album, Discography
import requests
from bs4 import BeautifulSoup

import gevent.monkey
gevent.monkey.patch_socket()
from gevent.pool import Pool
from timeit import default_timer

class LyricsProvider:
    def get_page(self, url):
        try:
            req = requests.get(url)
        except:
            req = None
            print('Unable to download url ' + url)
        return req

    def get_lyrics(self, author):
        pass

    def get_artist_page(self, author):
        pass

    def get_album_page(self, author, album):
        pass

    def get_lyrics_page(self, author, album, title):
        pass

    def extract_lyrics(self, song):
        pass


class LyricWiki(LyricsProvider):
    base_url = 'http://lyrics.wikia.com'

    def clean_string(self, text):
        text = text.replace('#', 'Number_').replace('[', '(').replace(']', ')').replace('{', '(').replace('}', ')')
        text = text.replace(' ', '_')
        return text

    def get_artist_page(self, author):
        author = self.clean_string(author)
        url = self.base_url + '/wiki/' + author
        artist_page = BeautifulSoup(self.get_page(url).text, 'lxml')
        if artist_page.find("div", {'class': 'noarticletext'}):
            return None
        return artist_page

    def get_album_page(self, author, album):
        author = self.clean_string(author)
        album = self.clean_string(album)
        url = self.base_url + '/wiki/' + author + ':' + album
        album_page = BeautifulSoup(self.get_page(url).text, 'lxml')
        if album_page.find("div", {'class': 'noarticletext'}):
            return None
        return album_page

    def get_lyrics_page(self, url):
        lyrics_page = BeautifulSoup(self.get_page(url).text, 'lxml')
        if lyrics_page.find("div", {'class': 'noarticletext'}):
            return None
        return lyrics_page

    def extract_lyrics(self, song):
        lyric_box = song.find("div", {'class': 'lyricbox'})
        lyrics = lyric_box.text
        return lyrics

    def get_songs(self, album):
        parent_node = album.parent
        while parent_node.name != 'ol':
            parent_node = parent_node.next_sibling
        song_links = parent_node.find_all('li')
        return song_links

    def create_song(self, link, author, album_title):
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
        artist_page = self.get_artist_page(author)
        if not artist_page:
            return None
        albums = [tag for tag in artist_page.find_all("span", {'class': 'mw-headline'}) if
                  tag.attrs['id'] not in ('Additional_information', 'External_links')]
        album_objects = []
        for elmt in albums:
            print('Downloading {0}'.format(elmt.text))
            album_title = elmt.text
            song_links = self.get_songs(elmt)
            pool = Pool(25)
            results = [pool.spawn(self.create_song, *(link, author, album_title)) for link in song_links]
            songs = [song.value for song in results]
            pool.join()
            # songs = [self.create_song(link, author, album_title) for link in song_links]
            album = Album(album_title, author, songs)
            album_objects.append(album)
        discography = Discography(author, album_objects)
        return discography




if __name__ == "__main__":
    test = LyricWiki()
    artist = test.get_artist_page('2Pac')
    album = test.get_album_page('2Pac', 'Me Against The World (1995)')
    lyrics_page = test.get_lyrics_page('http://lyrics.wikia.com/wiki/2Pac:Young_Black_Male')
    lyrics = test.extract_lyrics(lyrics_page)
    test_wikia = test.get_lyrics('Reggie Watts')
    pass
