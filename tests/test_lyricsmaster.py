#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `lyricsmaster` package."""

import os
import sys
import codecs

import pytest
from click.testing import CliRunner

from bs4 import BeautifulSoup, Tag

import requests

from lyricsmaster import models
from lyricsmaster import cli
from lyricsmaster import lyricsmaster
from lyricsmaster.utils import TorController, normalize

try:
    basestring # Python 2.7 compatibility
except NameError:
    basestring = str

python_is_outdated = '2.7' in sys.version or '3.3' in sys.version
is_appveyor = 'APPVEYOR' in os.environ
is_travis = 'TRAVIS' in os.environ


@pytest.fixture(scope="module")
def songs():
    songs = [models.Song(real_singer['songs'][0]['song'], real_singer['album'], real_singer['name'],
                         real_singer['songs'][0]['lyrics']),
             models.Song(real_singer['songs'][1]['song'], real_singer['album'], real_singer['name'],
                         real_singer['songs'][1]['lyrics'])]
    return songs


real_singer = {'name': 'The Notorious B.I.G.', 'album': 'Ready to Die (1994)',
               'songs': [{'song': 'Things Done Changed', 'lyrics': 'Remember back in the days...'},
                         {'song': 'Things Done Changed', 'lyrics': 'Remember back in the days...'}]
               }
fake_singer = {'name': 'Fake Rapper', 'album': "In my mom's basement", 'song': 'I fap',
               'lyrics': 'Everyday I fap furiously...'}


class TestSongs:
    """Tests for Song Class."""
    song = songs()[0]

    def test_song(self):
        assert self.song.__repr__() == 'lyricsmaster.models.Song({0}, {1}, {2})'.format(real_singer['songs'][0]['song'],
                                                                                        real_singer['album'],
                                                                                        real_singer['name'])

    def test_song_save(self):
        self.song.save()
        path = os.path.join(os.path.expanduser("~"), 'Documents', 'LyricsMaster', normalize(real_singer['name']),
                            normalize(real_singer['album']), 'Things-Done-Changed.txt')
        assert os.path.exists(path)
        folder = os.path.join(os.path.expanduser("~"), 'Documents', 'test_lyricsmaster_save')
        self.song.save(folder)
        path = os.path.join(folder, 'LyricsMaster', normalize(real_singer['name']), normalize(real_singer['album']),
                            'Things-Done-Changed.txt')
        assert os.path.exists(path)
        with codecs.open(path, 'r', encoding='utf-8') as file:
            assert self.song.lyrics == file.readlines()[0]


class TestAlbums:
    """Tests for Album Class."""

    songs = songs()
    album = models.Album(real_singer['album'], real_singer['name'], songs)

    def test_album(self):
        assert self.album.__idx__ == 0
        assert self.album.title == real_singer['album']
        assert self.album.author == real_singer['name']
        assert self.album.__repr__() == 'lyricsmaster.models.Album({0}, {1})'.format(real_singer['album'],
                                                                                     real_singer['name'])

    def test_album_isiter(self):
        assert len(self.album) == 2
        assert [elmt for elmt in self.album] == self.songs
        for x, y in zip(reversed(self.album), reversed(self.album.songs)):
            assert x == y

    def test_album_save(self):
        self.album.save()
        for song in self.album.songs:
            author = normalize(song.author)
            album = normalize(song.album)
            title = normalize(song.title)
            path = os.path.join(os.path.expanduser("~"), 'Documents', 'LyricsMaster', author, album, title + '.txt')
            assert os.path.exists(path)
            with codecs.open(path, 'r', encoding='utf-8') as file:
                assert song.lyrics == '\n'.join(file.readlines())


class TestDiscography:
    """Tests for Discography Class."""

    albums = [models.Album(real_singer['album'], real_singer['name'], songs()),
              models.Album(fake_singer['album'], fake_singer['name'], songs())]
    discography = models.Discography(real_singer['name'], albums)

    def test_discography(self):
        assert self.discography.__repr__() == 'lyricsmaster.models.Discography({0})'.format(real_singer['name'])

    def test_discography_isiter(self):
        assert self.discography.__idx__ == 0
        assert len(self.discography) == 2
        assert [elmt for elmt in self.discography] == self.albums
        for x, y in zip(reversed(self.discography), reversed(self.discography.albums)):
            assert x == y

    def test_discography_save(self):
        self.discography.save()
        for album in self.albums:
            for song in album.songs:
                author = normalize(song.author)
                album = normalize(song.album)
                title = normalize(song.title)
                path = os.path.join(os.path.expanduser("~"), 'Documents', 'LyricsMaster', author, album, title + '.txt')
                assert os.path.exists(path)
                with codecs.open(path, 'r', encoding='utf-8') as file:
                    assert song.lyrics == '\n'.join(file.readlines())


class TestLyricWiki:
    """Tests for LyricWiki Class."""

    provider = lyricsmaster.LyricWiki()
    clean = provider._clean_string

    def test_get_page(self):
        url = 'http://non-existent-url.com'
        request = self.provider.get_page(url)
        assert request is None
        request = self.provider.get_page('http://www.google.com')
        assert request.status == 200

    def test_clean_string(self):
        assert self.provider._clean_string(real_singer['name']) == 'The_Notorious_B.I.G.'

    def test_has_artist(self):
        url = 'http://lyrics.wikia.com/wiki/{0}'.format(self.clean(real_singer['name']))
        page = BeautifulSoup(requests.get(url).text, 'lxml')
        assert self.provider._has_artist(page)
        url = 'http://lyrics.wikia.com/wiki/{0}'.format(self.clean(fake_singer['name']))
        page = BeautifulSoup(requests.get(url).text, 'lxml')
        assert not self.provider._has_artist(page)

    def test_make_artist_url(self):
        assert self.provider._make_artist_url(
            self.clean(real_singer['name'])) == 'http://lyrics.wikia.com/wiki/The_Notorious_B.I.G.'

    def test_get_artist_page(self):
        page = self.provider.get_artist_page(real_singer['name'])
        assert '<!doctype html>' in str(page)
        page = self.provider.get_artist_page(fake_singer['name'])
        assert page is None

    def test_get_album_page(self):
        page = self.provider.get_album_page(real_singer['name'], fake_singer['album'])
        assert page is None
        page = self.provider.get_album_page(fake_singer['name'], fake_singer['album'])
        assert page is None
        page = self.provider.get_album_page(real_singer['name'], real_singer['album'])
        assert '<!doctype html>' in str(page)

    def test_has_lyrics(self):
        url = 'http://lyrics.wikia.com/wiki/{0}:{1}'.format(self.clean(real_singer['name']),
                                                            self.clean(real_singer['songs'][0]['song']))
        page = BeautifulSoup(requests.get(url).text, 'lxml')
        assert self.provider._has_lyrics(page)
        url = 'http://lyrics.wikia.com/wiki/{0}:{1}'.format(self.clean(real_singer['name']),
                                                            self.clean(fake_singer['song']))
        page = BeautifulSoup(requests.get(url).text, 'lxml')
        assert not self.provider._has_lyrics(page)

    def test_get_lyrics_page(self):
        page = self.provider.get_lyrics_page(
            'http://lyrics.wikia.com/wiki/{0}:{1}'.format(self.clean(real_singer['name']),
                                                          self.clean(real_singer['songs'][0]['song'])))
        assert '<!doctype html>' in str(page)
        page = self.provider.get_lyrics_page(
            'http://lyrics.wikia.com/wiki/{0}:{1}'.format(self.clean(fake_singer['name']),
                                                          self.clean(fake_singer['song'])))
        assert page is None

    def test_get_albums(self):
        url = 'http://lyrics.wikia.com/wiki/{0}'.format(self.clean(real_singer['name']))
        page = requests.get(url).text
        albums = self.provider.get_albums(page)
        for album in albums:
            assert isinstance(album, Tag)

    def test_get_album_title(self):
        url = 'http://lyrics.wikia.com/wiki/{0}'.format(self.clean(real_singer['name']))
        page = requests.get(url).text
        album = self.provider.get_albums(page)[0]
        album_title = self.provider.get_album_title(album)
        assert album_title == real_singer['album']

    def test_extract_lyrics(self):
        page = self.provider.get_lyrics_page(
            'http://lyrics.wikia.com/wiki/{0}:{1}'.format(self.clean(real_singer['name']),
                                                          self.clean(real_singer['songs'][0]['song'])))
        lyrics = self.provider.extract_lyrics(page)
        assert isinstance(lyrics, basestring)
        assert 'Remember back in the days' in lyrics
        assert "Don't ask me why I'm motherfuckin stressed" in lyrics

    def test_get_songs(self):
        author_page = BeautifulSoup(self.provider.get_artist_page(real_singer['name']), 'lxml')
        album = [tag for tag in author_page.find_all("span", {'class': 'mw-headline'}) if
                 tag.attrs['id'] not in ('Additional_information', 'External_links')][0]
        song_links = self.provider.get_songs(album)
        for link in song_links:
            assert isinstance(link, Tag)

    def test_create_song(self):
        author_page = BeautifulSoup(self.provider.get_artist_page(real_singer['name']), 'lxml')
        album = [tag for tag in author_page.find_all("span", {'class': 'mw-headline'}) if
                 tag.attrs['id'] not in ('Additional_information', 'External_links')][0]
        song_links = self.provider.get_songs(album)
        song_links[-1].attrs['href'] = '/wiki/{0}:{1}_fake_url'.format(self.clean(real_singer['name']), self.clean(
            real_singer['songs'][0]['song']))  # add fake url to valid tag
        fail_song = self.provider.create_song(song_links[-1], real_singer['name'], real_singer['album'])
        assert fail_song is None
        good_song = self.provider.create_song(song_links[1], real_singer['name'], real_singer['album'])
        assert isinstance(good_song, models.Song)
        assert good_song.title == real_singer['songs'][0]['song']
        assert good_song.album == real_singer['album']
        assert good_song.author == real_singer['name']
        assert 'Remember back in the days' in good_song.lyrics
        assert "Don't ask me why I'm motherfuckin stressed" in good_song.lyrics
        # Tests existing song with empty lyrics
        tag = '<a href="http://lyrics.wikia.com/wiki/Reggie_Watts:Feel_The_Same" class="new" title="Reggie Watts:Feel The Same (page does not exist)">Feel the Same</a>'
        page = BeautifulSoup(tag, 'lxml')
        page.attrs['title'] = "Reggie Watts:Feel The Same (page does not exist)"
        page.attrs['href'] = "http://lyrics.wikia.com/wiki/Reggie_Watts:Feel_The_Same"
        non_existent_song = self.provider.create_song(page, real_singer['name'], real_singer['album'])
        assert non_existent_song == None

    def test_get_lyrics(self):
        discography = self.provider.get_lyrics(
            'Reggie Watts')  # put another realsinger who has not so many songs to speed up testing.
        assert isinstance(discography, models.Discography)
        discography = self.provider.get_lyrics(fake_singer['name'])
        assert discography is None


class Test_tor:
    """Tests for Tor functionality."""
    tor_basic = TorController()
    if is_travis or (is_appveyor and python_is_outdated):
        tor_advanced = TorController(controlport='/var/run/tor/control', password='password')
    else:
        tor_advanced = TorController(controlport=9051, password='password')

    provider = lyricsmaster.LyricWiki(tor_basic)
    provider2 = lyricsmaster.LyricWiki(tor_advanced)

    @pytest.mark.skipif(is_appveyor and python_is_outdated, reason="Tor error on 2.7 and 3.3.")
    def test_anonymisation(self):
        anonymous_ip = self.provider.get_page("http://httpbin.org/ip").data
        real_ip = requests.get("http://httpbin.org/ip").text
        assert real_ip != anonymous_ip

    # this function is tested out in travis using a unix path as a control port instead of port 9051.
    # for now gets permission denied on '/var/run/tor/control' in Travis CI
    @pytest.mark.skipif(is_travis or (is_appveyor and python_is_outdated), reason="Skip this Tor test when in CI")
    def test_renew_tor_session(self):
        anonymous_ip = self.provider2.get_page("http://httpbin.org/ip").data
        real_ip = requests.get("http://httpbin.org/ip").text
        assert real_ip != anonymous_ip
        new_tor_circuit = self.provider2.tor_controller.renew_tor_circuit()
        anonymous_ip2 = self.provider2.get_page("http://httpbin.org/ip").data
        real_ip2 = requests.get("http://httpbin.org/ip").text
        assert real_ip2 != anonymous_ip2
        assert new_tor_circuit == True

    @pytest.mark.skipif(is_appveyor and python_is_outdated, reason="Tor error on 2.7 and 3.3.")
    def test_get_lyrics_tor_basic(self):
        discography = self.provider.get_lyrics(
            'Reggie Watts')  # put another realsinger who has not so many songs to speed up testing.
        assert isinstance(discography, models.Discography)

    @pytest.mark.skipif(is_travis or (is_appveyor and python_is_outdated), reason="Skip this Tor test when in CI")
    def test_get_lyricstor_advanced(self):
        discography = self.provider2.get_lyrics(
            'Reggie Watts')  # put another realsinger who has not so many songs to speed up testing.
        assert isinstance(discography, models.Discography)


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'lyricsmaster.cli.main' in result.output
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output
