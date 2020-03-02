import os
import pathlib
import random


class Mp3Index(object):
    """
    An index of MP3 files in a given directory, capable of yielding a file path at random
    """
    def __init__(self, parentdir):
        self.files = []
        for root, dirs, files in os.walk(parentdir):
            self.files.extend([pathlib.Path(root) / file for file in files if file.endswith('.mp3')])
