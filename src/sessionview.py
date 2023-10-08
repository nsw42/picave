from collections import namedtuple
from datetime import timedelta
import logging
import os.path
from typing import Tuple, Union
import urllib.parse

# pylint: disable=wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-position

from config import Config  # noqa: E402
from colournames import colour_names  # noqa: E402
import jsonfeed  # noqa: E402
from utils import parse_duration  # noqa: E402


Interval = namedtuple('Interval',
                      'name, type, cadence, effort, effort_val, duration, color, start_offset')


class SessionView(Gtk.DrawingArea):
    def __init__(self, config: Config, feed_url: str):
        super().__init__()
        self.config = config
        self.feed_url = feed_url
        self.colour_names = colour_names(os.path.join(os.path.dirname(__file__), 'rgb.txt'))

    def read_intervals(self, video_id):
        # Read the JSON of the main session
        urlparts = urllib.parse.urlparse(self.feed_url)
        new_leaf = f'{video_id}.json'
        slash = urlparts.path.rfind('/')
        new_path = urlparts.path[:slash + 1] + new_leaf
        urlparts = urlparts._replace(path=new_path)
        uri = urllib.parse.urlunparse(urlparts)
        try:
            session = jsonfeed.read_from_uri(uri, 'session.schema.json')
        except jsonfeed.NotFoundError as e:
            logging.error(f"{uri} could not be read: {e.message}")
            return []
        # Convert into an appropriately tailored list of Interval objects
        session = [Interval(start_offset=0, effort_val=0, **interval) for interval in session]
        session = [interval._replace(duration=parse_duration(interval.duration)) for interval in session]
        start_offset = 0
        for index, interval in enumerate(session):
            interval = interval._replace(start_offset=timedelta(seconds=start_offset))
            if isinstance(interval.color, str):
                interval = interval._replace(color=self.colour_names[interval.color])
            start_offset += interval.duration
            # Calculate effort (string) and effort_val (numeric watts)
            if interval.type == r'%FTP':
                assert interval.effort.endswith('%')
                effort, effort_val = self.interval_effort(video_id, interval.effort)
                # effort is something like "123%"
            elif interval.type == 'MAX':
                custom_max_effort = self.config.get_power(video_id, 'MAX', expand_default=True)
                if custom_max_effort:
                    effort, effort_val = self.interval_effort(video_id, custom_max_effort)
                else:
                    effort = interval.type
                    effort_val = float("inf")
                # effort is None, "123" (absolute power) or "456%" (relative to FTP)
            else:
                assert False
            interval = interval._replace(effort=effort, effort_val=effort_val)
            session[index] = interval
        return session

    def interval_effort(self, video_id: str, effort_desc: Union[int, str]) -> Tuple[str, int]:
        """
        Convert effort_desc, which is either an absolute power in watts (e.g. "400" or 400)
        or a value relative to FTP (e.g. "150%").
        Return a 2-tuple: the string describing the power, and the numeric version of the absolute watts
        """
        if isinstance(effort_desc, str) and effort_desc.endswith('%'):
            ftp = self.config.get_power(video_id, 'FTP', expand_default=True)
            assert ftp is not None
            percent_ftp = effort_desc[:-1]
            effort_val = int(ftp * float(percent_ftp) / 100.0)
            effort = f'{effort_val}W ({effort_desc})'
        else:
            effort_val = int(effort_desc)
            effort = f'{effort_val}W'
        return effort, effort_val
