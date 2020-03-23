from collections import namedtuple

import jsonfeed

VideoFeedItem = namedtuple('VideoFeedItem', ['name', 'id', 'url', 'date', 'duration', 'type'])


class VideoFeed(object):
    def __init__(self, url):
        self.url = url

        json_content = jsonfeed.read_from_uri(url, 'videofeed.schema.json')
        self.items = []
        for item in json_content:
            self.items.append(VideoFeedItem(**item))

    def __iter__(self):
        return self.items.__iter__()
