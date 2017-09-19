#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `lyricsmaster` package."""

import pytest
from click.testing import CliRunner

from bs4 import BeautifulSoup, Tag

import requests

from lyricsmaster import lyricsmaster
from lyricsmaster import cli
from lyricsmaster import lyricsprovider

try:
    basestring
except NameError:
    basestring = str


@pytest.fixture(scope="module")
def songs():
    songs = [lyricsmaster.Song('Bad Love', 'Bad news is coming', 'Luther Alison', None),
             lyricsmaster.Song('Ragged and dirty', 'Bad news is coming', 'Luther Alison', None),
             lyricsmaster.Song('Red rooster', 'Bad news is coming', 'Luther Alison', None),
             lyricsmaster.Song('Life is bitch', 'Bad news is coming', 'Luther Alison', None)]
    return songs


real_singer = {'name': 'Reggie Watts', 'album': 'Simplified (2004)', 'song': 'Your_Name'}
fake_singer = {'name': 'Fake Rapper', 'album': "In my mom's basement", 'song': 'I fap'}


class TestSongs:
    """Tests for Song Class."""
    song = lyricsmaster.Song('Bad Love', 'Bad news is coming', 'Luther Alison', None)

    def test_song(self):
        assert self.song.__repr__() == 'Song Object: Bad Love'


class TestAlbums:
    """Tests for Album Class."""

    songs = songs()
    album = lyricsmaster.Album('Bad news is coming', 'Luther Alison', songs)

    def test_album(self):
        assert self.album.idx == 0
        assert self.album.title == 'Bad news is coming'
        assert self.album.author == 'Luther Alison'
        assert self.album.__repr__() == 'Album Object: Bad news is coming'

    def test_album_isiter(self):
        assert len(self.album) == 4
        assert [elmt for elmt in self.album] == self.songs
        for x, y in zip(reversed(self.album), reversed(self.album.songs)):
            assert x == y


class TestDiscography:
    """Tests for Discography Class."""

    albums = [lyricsmaster.Album('Bad news is coming', 'Luther Alison', songs),
              lyricsmaster.Album('Bad news is coming', 'Luther Alison', songs)]
    discography = lyricsmaster.Discography('Luther Allison', albums)

    def test_discography(self):
        assert self.discography.__repr__() == 'Discography Object: Luther Allison'

    def test_discography_isiter(self):
        assert len(self.discography) == 2
        assert [elmt for elmt in self.discography] == self.albums
        for x, y in zip(reversed(self.discography), reversed(self.discography.albums)):
            assert x == y


class TestLyricWiki:
    provider = lyricsprovider.LyricWiki()

    def test_get_page(self):
        url = 'http://non-existent-url.com'
        request = self.provider.get_page(url)
        assert request is None
        request = self.provider.get_page('http://www.google.com')
        assert request.status_code == 200

    def test_clean_string(self):
        assert self.provider.clean_string('Reggie Watts {(#5)}') == 'Reggie_Watts_((Number_5))'

    def test_get_artist_page(self):
        page = self.provider.get_artist_page(real_singer['name'])
        assert isinstance(page, BeautifulSoup)
        page = self.provider.get_artist_page(fake_singer['name'])
        assert page is None

    def test_get_album_page(self):
        page = self.provider.get_album_page(real_singer['name'], real_singer['album'])
        assert page is None
        page = self.provider.get_album_page(fake_singer['name'], fake_singer['album'])
        assert page is None
        page = self.provider.get_album_page('2Pac', 'Me Against The World (1995)')
        assert isinstance(page, BeautifulSoup)

    def test_get_lyrics_page(self):
        page = self.provider.get_lyrics_page(
            'http://lyrics.wikia.com/wiki/{0}:{1}'.format(real_singer['name'], real_singer['song']))
        assert isinstance(page, BeautifulSoup)
        page = self.provider.get_lyrics_page(
            'http://lyrics.wikia.com/wiki/{0}:{1}'.format(fake_singer['name'], fake_singer['song']))
        assert page is None

    def test_extract_lyrics(self):
        page = self.provider.get_lyrics_page(
            'http://lyrics.wikia.com/wiki/{0}:{1}'.format(real_singer['name'], real_singer['song']))
        lyrics = self.provider.extract_lyrics(page)
        assert isinstance(lyrics, basestring)
        assert 'I recall the day' in lyrics
        assert "And I hope you'll stay." in lyrics

    def test_get_songs(self):
        author_page = self.provider.get_artist_page(real_singer['name'])
        album = [tag for tag in author_page.find_all("span", {'class': 'mw-headline'}) if
                 tag.attrs['id'] not in ('Additional_information', 'External_links')][0]
        song_links = self.provider.get_songs(album)
        for link in song_links:
            assert isinstance(link, Tag)

    def test_create_song(self):
        author_page = self.provider.get_artist_page(real_singer['name'])
        album = [tag for tag in author_page.find_all("span", {'class': 'mw-headline'}) if
                 tag.attrs['id'] not in ('Additional_information', 'External_links')][0]
        song_links = self.provider.get_songs(album)
        fail_song = self.provider.create_song(song_links[0], real_singer['name'], real_singer['album'])
        assert fail_song is None
        good_song = self.provider.create_song(song_links[9], real_singer['name'], real_singer['album'])
        assert isinstance(good_song, lyricsmaster.Song)
        assert good_song.title == 'Reggie Watts:Your Name'
        assert good_song.album == "Simplified (2004)"
        assert good_song.author == 'Reggie Watts'
        assert 'I recall the day' in good_song.lyrics
        assert "And I hope you'll stay." in good_song.lyrics

    def test_get_lyrics(self):
        discography = self.provider.get_lyrics(real_singer['name'])
        assert isinstance(discography, lyricsmaster.Discography)


class Test_tor:
    provider = lyricsprovider.LyricWiki(tor=True, controlport=9051, password='password')
    provider2 = lyricsprovider.LyricWiki(tor=True)
    def test_anonymisation(self):
        real_ip = self.provider.get_page("http://httpbin.org/ip").text
        anonymous_ip = requests.get("http://httpbin.org/ip").text
        assert real_ip != anonymous_ip

    # this function is greyed out in travis until i can enable ControlPort on Travis VM.
    # def test_renew_tor_session(self):
    #     anonymous_ip = self.provider.get_page("http://httpbin.org/ip").text
    #     real_ip = requests.get("http://httpbin.org/ip").text
    #     assert real_ip != anonymous_ip
    #     new_tor_circuit = self.provider.renew_tor_circuit(9051, 'password')
    #     anonymous_ip2 = self.provider.get_page("http://httpbin.org/ip").text
    #     real_ip2 = requests.get("http://httpbin.org/ip").text
    #     assert real_ip2 != anonymous_ip2
    #     assert new_tor_circuit == True

    def test_get_lyrics(self):
        discography = self.provider2.get_lyrics(real_singer['name'])
        assert isinstance(discography, lyricsmaster.Discography)





def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'lyricsmaster.cli.main' in result.output
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output


