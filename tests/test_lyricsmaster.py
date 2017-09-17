#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `lyricsmaster` package."""


from collections import Iterable
import pytest
from click.testing import CliRunner

from bs4 import BeautifulSoup, Tag

from lyricsmaster import lyricsmaster
from lyricsmaster import cli
from lyricsmaster import lyricsprovider

try:
  basestring
except NameError:
  basestring = str

@pytest.fixture(scope="module")
def songs():
    songs = [lyricsmaster.Song('Bad Love', 'Bad news is coming','Luther Alison', None),
             lyricsmaster.Song('Ragged and dirty', 'Bad news is coming', 'Luther Alison', None),
             lyricsmaster.Song('Red rooster', 'Bad news is coming', 'Luther Alison', None),
             lyricsmaster.Song('Life is bitch', 'Bad news is coming', 'Luther Alison', None)]
    return songs

class TestSongs:
    """Tests for Song Class."""
    song = lyricsmaster.Song('Bad Love', 'Bad news is coming','Luther Alison', None)

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


class TestDiscography:
    """Tests for Album Class."""

    albums = [lyricsmaster.Album('Bad news is coming', 'Luther Alison', songs),
                       lyricsmaster.Album('Bad news is coming', 'Luther Alison', songs)]
    discography = lyricsmaster.Discography('Luther Allison', albums)

    def test_discography(self):
        assert  self.discography.__repr__() == 'Discography Object: Luther Allison'

    def test_discography_isiter(self):
        assert len(self.discography) == 2
        assert [elmt for elmt in self.discography] == self.albums

class TestLyricWiki:
    provider = lyricsprovider.LyricWiki()
    author = 'Reggie Watts'

    def test_clean_string(self):
        assert self.provider.clean_string('Reggie Watts {(#5)}') == 'Reggie_Watts_((Number_5))'

    def test_get_artist_page(self):
        page = self.provider.get_artist_page(self.author)
        assert isinstance(page, BeautifulSoup)

    def test_get_album_page(self):
        page = self.provider.get_album_page('Reggie Watts', 'Simplified (2004)')
        assert isinstance(page, BeautifulSoup)

    def test_get_lyrics_page(self):
        page = self.provider.get_lyrics_page('http://lyrics.wikia.com/wiki/Reggie_Watts:Your_Name')
        assert isinstance(page, BeautifulSoup)

    def test_extract_lyrics(self):
        page = self.provider.get_lyrics_page('http://lyrics.wikia.com/wiki/Reggie_Watts:Your_Name')
        lyrics = self.provider.extract_lyrics(page)
        assert isinstance(lyrics, basestring)
        assert 'I recall the day' in lyrics
        assert "And I hope you'll stay." in lyrics

    def test_get_songs(self):
        author_page = self.provider.get_artist_page(self.author)
        album = [tag for tag in author_page.find_all("span", {'class': 'mw-headline'}) if
                  tag.attrs['id'] not in ('Additional_information', 'External_links')][0]
        song_links = self.provider.get_songs(album)
        for link in song_links:
            assert isinstance(link, Tag)

    def test_create_song(self):
        author_page = self.provider.get_artist_page(self.author)
        album = [tag for tag in author_page.find_all("span", {'class': 'mw-headline'}) if
                 tag.attrs['id'] not in ('Additional_information', 'External_links')][0]
        song_links = self.provider.get_songs(album)
        fail_song = self.provider.create_song(song_links[0], self.author, "Simplified (2004)")
        assert fail_song is None
        good_song = self.provider.create_song(song_links[9], self.author, "Simplified (2004)")
        assert isinstance(good_song, lyricsmaster.Song)
        assert good_song.title == 'Reggie Watts:Your Name'
        assert good_song.album == "Simplified (2004)"
        assert good_song.author == self.author
        assert 'I recall the day' in good_song.lyrics
        assert "And I hope you'll stay." in good_song.lyrics

    def test_get_lyrics(self):
        discography = self.provider.get_lyrics(self.author)
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
