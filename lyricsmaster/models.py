# -*- coding: utf-8 -*-

"""Models the domain objects.

Defines classes for Song, Album and Discography.

"""

import os
from codecs import open
from .utils import set_save_folder, normalize


class Song(object):
    """
    Song class.

    :param title: string.
        Song title.
    :param album: string.
        Album title.
    :param artist: string.
        Author name.
    :param lyrics: string.
        Lyrics of the song.
    :param writers: string.
        List of the song's writers.
    """
    __slots__ = ('title', 'album', 'artist', 'lyrics', 'writers')

    def __init__(self, title, album, artist, lyrics=None, writers=None):
        self.title = title
        self.album = album
        self.artist = artist
        self.lyrics = lyrics
        self.writers = writers

    def __repr__(self):
        return '{0}.{1}({2}, {3}, {4})'.format(__name__, self.__class__.__name__, self.title, self.album, self.artist)

    def save(self, folder=None):
        """
        Saves the lyrics of the song in the supplied folder.
        If no folder is supplied, 'folder' is set to {user}/Documents/lyricsmaster/
        The lyrics of a song are saved in the folder /artist/album/song_title.txt

        :param folder: string.
            path to save folder.
        """
        folder = set_save_folder(folder)
        if self.lyrics:
            artist = normalize(self.artist)
            album = normalize(self.album)
            save_path = os.path.join(folder, artist, album)
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            file_name = normalize(self.title)
            with open(os.path.join(save_path, file_name + ".txt"), "w", encoding="utf-8") as file:
                file.write(self.lyrics)


class Album(object):
    """
    Album Class.
    The Album class follows the Iterable protocol and can be iterated over the songs.

    :param title: string.
        Album title.
    :param artist: string.
        Artist name.
    :param release_date: string.
        Release date.
    :param songs: list.
        List of Songs objects.
    """
    __slots__ = ('__idx__', 'title', 'artist', 'release_date', 'songs')

    def __init__(self, title, artist, songs, release_date='Unknown'):
        self.__idx__ = 0
        self.title = title
        self.artist = artist
        self.release_date = release_date
        self.songs = songs

    def __repr__(self):
        return '{0}.{1}({2}, {3})'.format(__name__, self.__class__.__name__, self.title, self.artist)

    def __len__(self):
        return len(self.songs)

    def __getitem__(self, key):
        return self.songs[key]

    def __setitem__(self, key, value):
        if not isinstance(value, Song):
            raise TypeError
        else:
            self.songs[key] = value
        return

    def __delitem__(self, key):
        del self.songs[key]
        return

    def __iter__(self):
        return self

    def __next__(self):
        self.__idx__ += 1
        try:
            return self.songs[self.__idx__ - 1]
        except IndexError:
            self.__idx__ = 0
            raise StopIteration

    def __reversed__(self):
        return reversed(self.songs)

    next = __next__  # Python 2.7 compatibility for iterator protocol

    def save(self, folder=None):
        """
        Saves the album in the supplied folder.

        :param folder: string.
            path to save folder.
        """
        for song in self.songs:
            if song:
                song.save(folder)


class Discography(object):
    """
    Discography Class.
    The Discography class follows the Iterable protocol and can be iterated over the albums.

    :param artist: string.
        Artist name.
    :param albums: list.
        List of Album objects.
    """
    __slots__ = ('__idx__', 'artist', 'albums')

    def __init__(self, artist, albums):
        self.__idx__ = 0
        self.artist = artist
        self.albums = albums

    def __repr__(self):
        return '{0}.{1}({2})'.format(__name__, self.__class__.__name__, self.artist)

    def __len__(self):
        return len(self.albums)

    def __getitem__(self, key):
        return self.albums[key]

    def __setitem__(self, key, value):
        if not isinstance(value, Song):
            raise TypeError
        else:
            self.albums[key] = value
        return

    def __delitem__(self, key):
        del self.albums[key]
        return

    def __iter__(self):
        return self

    def __next__(self):
        self.__idx__ += 1
        try:
            return self.albums[self.__idx__ - 1]
        except IndexError:
            self.__idx__ = 0
            raise StopIteration

    def __reversed__(self):
        return reversed(self.albums)

    next = __next__  # Python 2.7 compatibility for iterator protocol

    def save(self, folder=None):
        """
        Saves Discography in the supplied folder.

        :param folder: string.
            Path to save folder.
        """
        for album in self.albums:
            album.save(folder)
