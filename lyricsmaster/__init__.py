# -*- coding: utf-8 -*-

"""Top-level package for LyricsMaster."""

__author__ = """SekouD"""
__email__ = 'sekoud.python@gmail.com'
__version__ = '2.8.0'

from .providers import LyricWiki, AzLyrics, Genius, MusixMatch, Lyrics007
from .utils import TorController

CURRENT_PROVIDERS = {'lyricwiki': LyricWiki,
                     'azlyrics': AzLyrics,
                     'genius': Genius,
                     'musixmatch': MusixMatch,
                     'lyrics007': Lyrics007,
                     }
