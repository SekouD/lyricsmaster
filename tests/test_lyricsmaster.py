#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `lyricsmaster` package."""


from collections import Iterable
import pytest
from click.testing import CliRunner

from lyricsmaster import lyricsmaster
from lyricsmaster import cli

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

def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'lyricsmaster.cli.main' in result.output
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output
