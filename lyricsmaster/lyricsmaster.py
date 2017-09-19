# -*- coding: utf-8 -*-

"""Main module."""


class Song:
    def __init__(self, title, album, author, lyrics):
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
