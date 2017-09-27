=====
Usage
=====

To use LyricsMaster in a project::

    from lyricsmaster import LyricWiki, TorController

    # Select a provider from the supported Lyrics Providers (LyricWiki, AzLyrics, Genius etc..)
    provider = LyricWiki()

    # Fetch all lyrics from 2Pac
    discography = provider.get_lyrics('2Pac')

    # Discography Objects and Album Objects can be iterated over.
    for album in discography:    # album is an Album Object.
        print(album)
        for song in album:       # song is a Song Object.
            print(song.lyrics)

    # Fetch all lyrics from 2pac's album 'All eyes on me'
    album = provider.get_lyrics('2Pac', album='All eyes on me')

    # Fetch the lyrics from 2pac's album 'All eyes on me' and song 'California Love'
    album = provider.get_lyrics('2Pac', album='All eyes on me', 'California Love)

    # Once the lyrics are fetched, you can save them on disk. The 'save()' method is implemented for Discography, Album and Song objects.
    # By default, the lyrics are saved in {user}/Documents/lyricsmaster/
    discography.save()

    # You can also supply a folder to save the lyrics in.
    folder = 'c:\MyFolder'
    discography.save(folder)

    # For anonymity, you can use a Tor Proxy to make requests.
    # The TorController class has the same defaults as a default Tor Install.
    provider = LyricWiki(TorController())
    discography = provider.get_lyrics('2Pac')

    # For enhanced anonymity, the TorController can renew the the Tor ciruit for each album dowloaded.
    # For this functionnality to work, the Tor ControlPort option must be enabled in your torrc config file.
    # See https://www.torproject.org/docs/tor-manual.html.en for more information.
    provider = LyricWiki(TorController(control_port=9051, password='password))
    discography = provider.get_lyrics('2Pac')



To use LyricsMaster from the command line::

    $ lyricsmaster <artist_name> options

Examples::

    $ lyricsmaster "Reggie Watts"

    $ lyricsmaster "Reggie Watts" --tor 127.0.0.1

    $ lyricsmaster "Reggie Watts" --tor 127.0.0.1 --controlport 9051 --password password
