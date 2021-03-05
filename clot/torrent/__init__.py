"""This package provides torrent-related functions and classes.

Torrent structure is described at the following addresses:

https://www.bittorrent.org/beps/bep_0003.html
https://www.bittorrent.org/beps/bep_0027.html

https://wiki.theory.org/BitTorrentSpecification#Metainfo_File_Structure
https://wiki.theory.org/index.php/Talk:BitTorrentSpecification

http://wiki.bitcomet.com/inside_bitcomet
"""


from .metainfo import Metainfo


def new():
    """Create an empty torrent."""
    return parse(b'de')


def parse(raw_bytes):
    """Create a torrent from a bytes-like object."""
    return Metainfo(raw_bytes)


def load(file_path):
    """Create a torrent from a file specified by the path-like object."""
    with open(file_path, 'rb') as readable:
        raw_bytes = readable.read()
    return Metainfo(raw_bytes, file_path)
