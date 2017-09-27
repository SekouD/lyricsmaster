# -*- coding: utf-8 -*-

"""Console script for lyricsmaster."""

import click
from lyricsmaster import LyricWiki, AzLyrics, Genius



@click.command()
@click.argument('artist_name')
@click.option('--provider', default=LyricWiki, help='Lyrics Provider.')
@click.option('--album', default=None, help='Album.')
@click.option('--song', default=None, help='Song.')
@click.option('--folder', default=None, help='Folder where the lyrics will be saved.')
def main(artist_name, provider, album, song, folder):
    """Console script for lyricsmaster."""
    # provider = provider()
    results = provider.get_lyrics(artist_name)
    results.save()


if __name__ == "__main__":
    main()
