# -*- coding: utf-8 -*-

"""Console script for lyricsmaster."""

import click
import lyricsmaster
from .utils import TorController
import sys
import logging


@click.command()
@click.argument('artist_name')
@click.option('-p', '--provider', default='LyricWiki', help='Lyrics Provider.', type=click.STRING)
@click.option('-a', '--album', default=None, help='Album.', type=click.STRING)
@click.option('-s', '--song', default=None, help='Song.', type=click.STRING)
@click.option('-f', '--folder', default=None, help='Folder where the lyrics will be saved.', type=click.STRING)
@click.option('--tor', default=None, help='Tor service Ip address.', type=click.STRING)
@click.option('--socksport', default=9050, help='Tor SocksPort.', type=click.INT)
@click.option('--controlport', default=None, help='Tor ControlPort.', type=click.INT)
@click.option('--controlpath', default=None, help='Tor ControlPath.', type=click.STRING)
@click.option('--password', default='', help='Password for Tor ControlPort.', type=click.STRING)
def main(artist_name, provider, album, song, folder, tor, socksport, controlport, controlpath, password):
    """Console script for lyricsmaster."""
    logger = logging.getLogger(__name__.split('.')[0])

    # create console handler and set level to debug
    console_handler = logging.StreamHandler(sys.stdout)
    error_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    error_handler.setLevel(logging.ERROR)
    logger.addHandler(console_handler)
    logger.addHandler(error_handler)
    logger.setLevel(logging.INFO)
    try:
        provider = lyricsmaster.CURRENT_PROVIDERS[provider.lower()]
    except KeyError as e:
        logger.warning('The provider {0} is not supported'.format(provider))
        return
    if tor:
        if controlport:
            provider_instance = provider(
                TorController(ip=tor, socksport=socksport, controlport=controlport, password=password))
        elif controlpath:
            provider_instance = provider(
                TorController(ip=tor, socksport=socksport, controlport=controlpath, password=password))
        else:
            provider_instance = provider(TorController(ip=tor, socksport=socksport))
    else:
        provider_instance = provider()
    results = provider_instance.get_lyrics(artist_name, album=album, song=song)
    results.save(folder=folder)


if __name__ == "__main__":
    main()
