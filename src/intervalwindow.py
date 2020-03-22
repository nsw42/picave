from collections import namedtuple
from datetime import datetime, timedelta
import urllib.parse

import jsonfeed
from utils import format_mm_ss

import cairo
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402 # need to call require_version before we can call this
gi.require_version('GLib', '2.0')
from gi.repository import GLib  # noqa: E402 # need to call require_version before we can call this


Interval = namedtuple('Interval', ['name', 'type', 'cadence', 'effort', 'duration', 'end_offset'])


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

        self.fontoptions = cairo.FontOptions()
        self.fontoptions.set_antialias(cairo.ANTIALIAS_SUBPIXEL)

        self.intervals = []
        self.start_time = None
        self.current_interval_index = None
        self.connect("draw", self.on_draw)

    def read_intervals(self, video_id):
        urlparts = urllib.parse.urlparse(self.feed_url)
        new_leaf = '%s.json' % video_id
        slash = urlparts.path.rfind('/')
        new_path = urlparts.path[:slash + 1] + new_leaf
        urlparts = urlparts._replace(path=new_path)
        uri = urllib.parse.urlunparse(urlparts)
        session = jsonfeed.read_from_uri(uri, 'session.schema.json')
        session = [Interval(end_offset=0, **interval) for interval in session]
        session = [interval._replace(duration=parse_duration(interval.duration)) for interval in session]
        end_offset = 0
        for index in range(len(session)):
            interval = session[index]
            end_offset += interval.duration
            interval = interval._replace(end_offset=timedelta(seconds=end_offset))
            session[index] = interval
        return session

    def play(self, video_id):
        self.intervals = self.read_intervals(video_id)
        self.start_time = datetime.now()
        self.current_interval_index = 0
        GLib.timeout_add_seconds(1, self.force_redraw)

    def force_redraw(self):
        if self.current_interval_index is None:
            return False  # don't call again, until restarted
        self.queue_draw()
        return True

    def on_draw(self, drawingarea, context: cairo.Context):
        now = datetime.now()

        while True:
            if self.current_interval_index is None:
                return

            interval = self.intervals[self.current_interval_index]
            interval_end_time = self.start_time + interval.end_offset

            if now < interval_end_time:
                break

            self.current_interval_index += 1
            if self.current_interval_index >= len(self.intervals):
                self.current_interval_index = None
                return
            # loop, to update interval, interval_start_time and interval_end

        interval_remaining = (interval_end_time - now).seconds

        context.select_font_face('Sans', cairo.FontSlant.NORMAL, cairo.FontWeight.NORMAL)
        context.set_antialias(cairo.Antialias.SUBPIXEL)
        context.set_font_size(24)  # TODO: units??

        x0 = 20
        yd = 30

        y = 20

        context.move_to(x0, y)
        context.show_text(interval.name)
        y += yd

        context.move_to(x0, y)
        context.show_text(interval.effort)
        y += yd

        context.move_to(x0, y)
        context.show_text('RPM: %u' % interval.cadence)
        y += yd

        context.move_to(x0, y)
        context.show_text(format_mm_ss(interval_remaining))
