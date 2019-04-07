=====
Usage
=====

To use LyricsMaster in a project::

    from lyricsmaster import LyricWiki, TorController


    # Select a provider from the supported Lyrics Providers (LyricWiki, AzLyrics, Genius etc..)
    # The default Provider is LyricWiki
    provider = LyricWiki()

    # Fetch all lyrics from 2Pac
    discography = provider.get_lyrics('2Pac')

    # Discography Objects and Album Objects can be iterated over.
    for album in discography:    # album is an Album Object.
        print('Album: ', album.title)
        for song in album:       # song is a Song Object.
            print('Song: ', song.title)
            print('Lyrics: ', song.lyrics)

    # New indexing and slicing support of Discography and Album Objects
    first_song_of_first_album = discography.albums[0].songs[0]
    lat_two_songs_of_first_album = discography.albums[0].songs[-2:]

    # Fetch all lyrics from 2pac's album 'All eyez on me'.
    album = provider.get_lyrics('2Pac', album='All eyes on me')

    # Fetch the lyrics from the song 'California Love' in 2pac's album 'All eyez on me'.
    song = provider.get_lyrics('2Pac', album='All eyez on me', song='California Love)

    # Once the lyrics are fetched, you can save them on disk.
    # The 'save()' method is implemented for Discography, Album and Song objects.
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



To use LyricsMaster from the command line (The default Lyrics Provider is LyricWiki)::

    $ lyricsmaster <artist_name> options

Examples::

    $ lyricsmaster "2Pac"
    Anonymous requests disabled. The connexion will not be anonymous.
    Downloading 2Pacalypse Now (1991)
    2Pacalypse Now (1991) succesfully downloaded
    Downloading Strictly 4 My N.I.G.G.A.Z... (1993)
    Strictly 4 My N.I.G.G.A.Z... (1993) succesfully downloaded
    Downloading Thug Life - Volume 1 (1994)
    ...


    $ lyricsmaster "2Pac" --provider Genius
    Anonymous requests disabled. The connexion will not be anonymous.
    Downloading The Rose That Grew From Concrete (Book)
    The Rose That Grew From Concrete (Book) succesfully downloaded
    Downloading Best of 2Pac Part 2: Life
    Best of 2Pac Part 2: Life succesfully downloaded
    ...


    $ lyricsmaster "2Pac" --tor 127.0.0.1
    Anonymous requests enabled. The Tor circuit will change according to the Tor network defaults.
    Downloading 2Pacalypse Now (1991)
    2Pacalypse Now (1991) succesfully downloaded
    Downloading Strictly 4 My N.I.G.G.A.Z... (1993)
    Strictly 4 My N.I.G.G.A.Z... (1993) succesfully downloaded
    Downloading Thug Life - Volume 1 (1994)
    ...


    $ lyricsmaster "2Pac" --tor 127.0.0.1 --controlport 9051 --password password
    Anonymous requests enabled. The Tor circuit will change for each album.
    New Tor circuit created
    Downloading 2Pacalypse Now (1991)
    2Pacalypse Now (1991) succesfully downloaded
    New Tor circuit created
    Downloading Strictly 4 My N.I.G.G.A.Z... (1993)
    Strictly 4 My N.I.G.G.A.Z... (1993) succesfully downloaded
    New Tor circuit created
    Downloading Thug Life - Volume 1 (1994)
    ...

