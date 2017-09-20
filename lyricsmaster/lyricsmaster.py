# -*- coding: utf-8 -*-

"""Main module."""

import os
import re


def normalize(value):
    """

    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.

    :param value: string
    :return: string
    """
    value = re.sub('[^\w\s-]', '', value).strip()
    value = re.sub('[-\s]+', '-', value)
    return value


def set_save_folder(folder):
    """

    :param folder: string folder path
    :return: string folder path
    """
    if not folder:
        folder = os.path.join(os.path.expanduser("~"), 'Documents', 'LyricsMaster')
    else:
        folder = os.path.join(folder, 'LyricsMaster')
    return folder


class Song:
    def __init__(self, title, album, author, lyrics=None):
        """

        :param title: string
        :param album: string
        :param author: string
        :param lyrics: string
        """
        self.title = title
        self.album = album
        self.author = author
        self.lyrics = lyrics

    def __repr__(self):
        return self.__class__.__name__ + " Object: " + self.title

    def save(self, folder=None):
        """

        :param folder: path to save folder
        """
        folder = set_save_folder(folder)
        if self.lyrics:
            author = normalize(self.author)
            album = normalize(self.album)
            save_path = os.path.join(folder, author, album)
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            file_name = normalize(self.title)
            with open(os.path.join(save_path, file_name + ".txt"), "w", encoding="utf-8") as file:
                file.write(self.lyrics)


class Album:
    def __init__(self, title, author, songs):
        """

        :param title: string
        :param author: string
        :param songs: string
        """
        self.idx = 0
        self.title = title
        self.author = author
        self.songs = songs

    def __repr__(self):
        return self.__class__.__name__ + " Object: " + self.title

    def __len__(self):
        return len(self.songs)

    def __iter__(self):
        return self

    def __next__(self):
        self.idx += 1
        try:
            return self.songs[self.idx - 1]
        except IndexError:
            self.idx = 0
            raise StopIteration

    def __reversed__(self):
        return reversed(self.songs)

    next = __next__

    def save(self, folder=None):
        """

        :param folder: path to save folder
        """
        for song in self.songs:
            if song:
                song.save(folder)


class Discography:
    def __init__(self, author, albums):
        """

        :param author: string
        :param albums: string
        """
        self.idx = 0
        self.author = author
        self.albums = albums

    def __repr__(self):
        return self.__class__.__name__ + " Object: " + self.author

    def __len__(self):
        return len(self.albums)

    def __iter__(self):
        return self

    def __next__(self):
        self.idx += 1
        try:
            return self.albums[self.idx - 1]
        except IndexError:
            self.idx = 0
            raise StopIteration

    def __reversed__(self):
        return reversed(self.albums)

    next = __next__

    def save(self, folder=None):
        """

        :param folder: path to save folder
        """
        for album in self.albums:
            album.save(folder)
