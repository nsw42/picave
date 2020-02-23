import json
from urllib.parse import urlparse

import requests


class VideoFeed(object):
    def __init__(self, json_content):
        self.feed = json_content  # TODO: Convert this into an actual object

    @staticmethod
    def init_from_feed_url(url):
        """
        Create and initialise a VideoFeed object from the url specified on the command-line
        This may be a file:// or http[s]://
        """
        try:
            parsed = urlparse(url)
        except ValueError:
            # TODO: Error handling
            raise
        if parsed.scheme == 'file':
            # read the file directory
            return VideoFeed.init_from_file(parsed.path)
        else:
            return VideoFeed.init_by_reading_url(url)

    @staticmethod
    def init_from_file(filename):
        """
        Create and initialise a VideoFeed object by reading a local file
        """
        try:
            handle = open(filename)
        except OSError:
            # TODO: Error handling
            raise
        content = json.load(handle)
        return VideoFeed(content)

    @staticmethod
    def init_by_reading_url(url):
        """
        Create and initialise a VideoFeed object by reading the given URL
        """
        response = requests.get(url)
        if response.status_code == 200:
            return VideoFeed(response.json())
        else:
            # TODO: Error handling
            raise Exception("Could not read %s" % url)
