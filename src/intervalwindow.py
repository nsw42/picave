from collections import namedtuple
import urllib.parse

import jsonfeed

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402 # need to call require_version before we can call this


Interval = namedtuple('Interval', ['name', 'type', 'cadence', 'effort', 'duration'])


def parse_duration(duration_str: str):
    '''
    >>> parse_duration('2s')
    2
    >>> parse_duration('1m')
    60
    >>> parse_duration('10m 5s')
    605
    >>> parse_duration('1h')
    3600
    >>> parse_duration('2h3m')
    7380
    >>> parse_duration('3h2m  1s')
    10921
    '''
    orig_duration_str = duration_str

    def strip_leading_fragment(duration_str: str):
        index = 0
        while duration_str[index].isdigit():
            index += 1
        return int(duration_str[:index]), duration_str[index], duration_str[index + 1:].strip()
    duration = 0
    while duration_str:
        nr, unit, duration_str = strip_leading_fragment(duration_str)
        if unit == 'h':
            duration += nr * 60 * 60
        elif unit == 'm':
            duration += nr * 60
        elif unit == 's':
            duration += nr
        else:
            raise ValueError("Invalid duration %s" % orig_duration_str)
    return duration


class IntervalWindow(Gtk.DrawingArea):
    def __init__(self, feed_url: str):
        super().__init__()
        self.feed_url = feed_url

        self.intervals = []
        self.start_time = None

    def read_intervals(self, video_id):
        urlparts = urllib.parse.urlparse(self.feed_url)
        new_leaf = '%s.json' % video_id
        slash = urlparts.path.rfind('/')
        new_path = urlparts.path[:slash + 1] + new_leaf
        urlparts = urlparts._replace(path=new_path)
        uri = urllib.parse.urlunparse(urlparts)
        session = jsonfeed.read_from_uri(uri, 'session.schema.json')
        session = [Interval(**interval) for interval in session]
        session = [interval._replace(duration=parse_duration(interval.duration)) for interval in session]
        return session

    def show(self, video_id):
        self.intervals = self.read_intervals(video_id)
