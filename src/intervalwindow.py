from collections import namedtuple
from datetime import datetime, timedelta
import urllib.parse

import jsonfeed
from utils import clip, format_mm_ss

import cairo
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402 # need to call require_version before we can call this
gi.require_version('GLib', '2.0')
from gi.repository import GLib  # noqa: E402 # need to call require_version before we can call this


Interval = namedtuple('Interval', ['name', 'type', 'cadence', 'effort', 'duration', 'start_offset'])


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
        session = [Interval(start_offset=0, **interval) for interval in session]
        session = [interval._replace(duration=parse_duration(interval.duration)) for interval in session]
        start_offset = 0
        for index in range(len(session)):
            interval = session[index]
            interval = interval._replace(start_offset=timedelta(seconds=start_offset))
            start_offset += interval.duration
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
            interval_start_time = self.start_time + interval.start_offset
            interval_end = interval_start_time + timedelta(seconds=interval.duration)

            if now < interval_end:
                break

            self.current_interval_index += 1
            if self.current_interval_index >= len(self.intervals):
                self.current_interval_index = None
                return
            # loop, to update interval, interval_start_time and interval_end

        interval_remaining = (interval_end - now).seconds
        interval_pct = (now - interval_start_time).seconds / interval.duration

        interval_h = drawingarea.get_allocated_height() * (1.0 - interval_pct)

        context.rectangle(0,
                          0,
                          drawingarea.get_allocated_width(),
                          interval_h)
        context.set_source_rgb(1.0, 0.0, 0.0)
        context.fill_preserve()
        context.set_source_rgb(0.0, 0.0, 0.0)
        context.stroke()

        context.select_font_face('Sans', cairo.FontSlant.NORMAL, cairo.FontWeight.NORMAL)
        context.set_antialias(cairo.Antialias.SUBPIXEL)
        context.set_font_size(24)  # TODO: units??

        x0 = 20
        y0 = 20
        y = self.show_interval(context, interval, x0, y0, interval_remaining)
        if self.current_interval_index + 1 < len(self.intervals):
            block_h = y - y0
            max_permitted_y = drawingarea.get_allocated_height() - block_h
            next_interval = self.intervals[self.current_interval_index + 1]
            self.show_interval(context,
                               next_interval,
                               x0,
                               clip(y, interval_h + 24, max_permitted_y),
                               next_interval.duration)

    def show_interval(self, context, interval, x0, y, interval_remaining):
        yd = 30

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
        y += yd
        return y
