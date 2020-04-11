from collections import namedtuple
from datetime import timedelta
import logging
import os.path
import urllib.parse

from config import Config
from colournames import ColourNames
import jsonfeed
from utils import parse_duration

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402 # need to call require_version before we can call this


Interval = namedtuple('Interval', ['name', 'type', 'cadence', 'effort', 'duration', 'color', 'start_offset'])


class SessionView(Gtk.DrawingArea):
    def __init__(self, config: Config, feed_url: str):
        super().__init__()
        self.config = config
        self.feed_url = feed_url
        self.colour_names = ColourNames(os.path.join(os.path.dirname(__file__), 'rgb.txt'))

    def read_intervals(self, video_id):
        urlparts = urllib.parse.urlparse(self.feed_url)
        new_leaf = '%s.json' % video_id
        slash = urlparts.path.rfind('/')
        new_path = urlparts.path[:slash + 1] + new_leaf
        urlparts = urlparts._replace(path=new_path)
        uri = urllib.parse.urlunparse(urlparts)
        try:
            session = jsonfeed.read_from_uri(uri, 'session.schema.json')
        except jsonfeed.NotFoundError as e:
            logging.warning("%s could not be read: %s" % (uri, e.message))
            return []
        session = [Interval(start_offset=0, **interval) for interval in session]
        session = [interval._replace(duration=parse_duration(interval.duration)) for interval in session]
        start_offset = 0
        for index in range(len(session)):
            interval = session[index]
            interval = interval._replace(start_offset=timedelta(seconds=start_offset))
            if isinstance(interval.color, str):
                interval = interval._replace(color=self.colour_names[interval.color])
            start_offset += interval.duration
            if interval.type == r'%FTP':
                assert interval.effort.endswith('%')
                effort = interval.effort[:-1]
                effort = int(effort)
                effort = self.config.ftp * effort / 100.0
                effort = '%uW (%s)' % (effort, interval.effort)
                interval = interval._replace(effort=effort)
            session[index] = interval
        return session
