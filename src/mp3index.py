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
        # TODO: Error if not self.files?
        self.generator_indices = None  # initialised if/when random_file() is called

    def random_file(self):
        if not self.files:
            return None
        if not self.generator_indices:
            self.generator_indices = list(range(len(self.files)))
            random.shuffle(self.generator_indices)
        index = self.generator_indices.pop(0)
        return self.files[index]
