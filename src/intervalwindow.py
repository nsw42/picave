from collections import namedtuple
from datetime import datetime, timedelta
import urllib.parse

from config import Config
import jsonfeed
from utils import format_mm_ss, parse_duration

import cairo
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402 # need to call require_version before we can call this
gi.require_version('GLib', '2.0')
from gi.repository import GLib  # noqa: E402 # need to call require_version before we can call this


Interval = namedtuple('Interval', ['name', 'type', 'cadence', 'effort', 'duration', 'color', 'start_offset'])


class IntervalWindow(Gtk.DrawingArea):
    def __init__(self, config: Config, feed_url: str):
        super().__init__()
        self.config = config
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
            if interval.type == r'%FTP':
                assert interval.effort.endswith('%')
                effort = interval.effort[:-1]
                effort = int(effort)
                effort = self.config.ftp * effort / 100.0
                effort = '%uW (%s)' % (effort, interval.effort)
                interval = interval._replace(effort=effort)
            session[index] = interval
        return session

    def play(self, video_id):
        self.intervals = self.read_intervals(video_id)
        self.start_time = datetime.now()
        self.current_interval_index = 0
        GLib.timeout_add_seconds(1, self.force_redraw)

    def force_redraw(self):
        if self.current_interval_index is None:
            return False  # don't call again until restarted
        self.queue_draw()
        return True

    def on_draw(self, drawingarea, context: cairo.Context):
        now = datetime.now()

        if self.current_interval_index is None:
            return

        while now >= (self.start_time
                      + self.intervals[self.current_interval_index].start_offset
                      + timedelta(seconds=self.intervals[self.current_interval_index].duration)):
            self.current_interval_index += 1
            if self.current_interval_index >= len(self.intervals):
                self.current_interval_index = None
                return

        text_h = 30
        block_h = text_h * 4

        y0 = 0
        one_minute_h = drawingarea.get_allocated_height() - block_h

        context.select_font_face('Sans', cairo.FontSlant.NORMAL, cairo.FontWeight.NORMAL)
        context.set_antialias(cairo.Antialias.SUBPIXEL)
        context.set_font_size(24)  # TODO: units??

        draw_interval_index = self.current_interval_index
        while draw_interval_index < len(self.intervals):
            draw_interval = self.intervals[draw_interval_index]
            interval_start_time = self.start_time + draw_interval.start_offset
            if interval_start_time < now:
                y = y0
            else:
                start_delta = interval_start_time - now
                y = y0 + (start_delta.seconds / 60) * one_minute_h
            if y > drawingarea.get_allocated_height():
                break

            if draw_interval_index == self.current_interval_index:
                draw_interval_end = (self.start_time
                                     + draw_interval.start_offset
                                     + timedelta(seconds=draw_interval.duration))
                draw_interval_remaining = (draw_interval_end - now).seconds
            else:
                draw_interval_remaining = draw_interval.duration
            h = draw_interval_remaining / 60.0 * one_minute_h

            context.rectangle(0,
                              y,
                              drawingarea.get_allocated_width(),
                              h)
            context.set_source_rgb(draw_interval.color[0] / 255.0,
                                   draw_interval.color[1] / 255.0,
                                   draw_interval.color[2] / 255.0)
            context.fill_preserve()
            context.set_source_rgb(0.0, 0.0, 0.0)
            context.stroke()

            text_x = 20  # offset the text slightly into the rectangle
            text_y = y + text_h
            context.move_to(text_x, text_y)
            context.show_text(draw_interval.name)
            text_y += text_h

            context.move_to(text_x, text_y)
            context.show_text(draw_interval.effort)
            text_y += text_h

            context.move_to(text_x, text_y)
            context.show_text('RPM: %u' % draw_interval.cadence)
            text_y += text_h

            context.move_to(text_x, text_y)
            context.show_text(format_mm_ss(draw_interval_remaining))
            text_y += text_h

            draw_interval_index += 1
