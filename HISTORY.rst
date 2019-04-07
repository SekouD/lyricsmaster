=======
History
=======


2.8.1 (2019-04-07)
-------------------

* Implemented more fully the Python Data Model for the Discography and Album classes.
* Now individual albums or songs in a Discography object can be individually accessed by indexing or slicing on top of previously being iterable.
* For example Discography.albums[0].songs[0] or Discography.albums[0].songs[2:5]
* Updated dependencies.

2.8 (2019-03-31)
-------------------

* Enhanced support for utf-8 characters even when the html encoding has wrong information. (see https://github.com/SekouD/lyricsmaster/issues/211)
* Fixed AzLyrics bug when Artist had song but no album on the service.
* Updated dependencies.

2.7.25 (2019-03-23)
-------------------

* Enhanced support for utf-8 characters even when the html encoding has wrong information. (see https://github.com/SekouD/lyricsmaster/issues/211)
* Fixed MusixMatch bug when only the first sentence of some lyrics was parsed.
* updated logger configuration to avoid repeated logs when lyricsmaster was used as a library instead of standalone.
* Updated dependencies.

2.7.24 (2019-03-16)
-------------------

* Fixed bug when trying to download lyrics from urls containing unicode characters. (see https://github.com/SekouD/lyricsmaster/issues/211)
* Replaced use of print() with Python logging facilities.
* Updated dependencies.

2.7.23 (2019-02-28)
-------------------

* Updated lyricsmaster to reflect changes in MusixMatch and Lyrics007 APIs.
* Updated dependencies.

2.7.22 (2018-11-18)
-------------------

* Updated dependencies.


2.7.21 (2018-11-04)
-------------------

* Updated to latest tor version.
* Updated dependencies.

2.7.20 (2018-07-29)
-------------------

* Updated to latest tor version.
* Updated documentation.


2.7.19 (2018-07-16)
-------------------

* Catch exceptions when the release date of the album is not in the title tag for all providers.


2.7.17 (2018-07-08)
-------------------

* Improved Tests.
* Updated documentation.


2.7.16 (2017-09-27)
-------------------

* General improvements.


2.7.0 (2017-09-27)
------------------

* Added Command Line Interface.

2.6.0 (2017-09-26)
------------------

* Added Genius provider.

2.5.0 (2017-09-26)
------------------

* Added python 2.7 compatibility

2.4.0 (2017-09-24)
------------------

* Added AzLyrics provider.

2.3.0 (2017-09-21)
------------------

* Added full documentation.
* Corrected asynchronous requests bug when renewing Tor circuit.

2.2.0 (2017-09-20)
------------------

* Added save method to Discography, Album, Song objects.

2.1.0 (2017-09-20)
------------------

* Added Asynchronous Requests.

2.0.0 (2017-09-19)
------------------

* Added Tor Anonymisation.

1.0.0 (2017-09-17)
------------------

* Added LyricWiki provider.

0.1.0 (2017-09-11)
------------------

* First release on PyPI.
