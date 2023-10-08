import cairo

from config import Config
from sessionview import SessionView


class SessionPreview(SessionView):
    def __init__(self, config: Config, feed_url: str):
        super().__init__(config, feed_url)
        self.intervals = []
        self.max_duration = 1
        self.connect("draw", self.on_draw)

    def show_session(self, video_id):
        self.intervals = self.read_intervals(video_id)
        if self.intervals:
            self.max_duration = self.intervals[-1].start_offset + self.intervals[-1].duration
            # intervals are returned in chronological order, but sort them
            # into desired order for drawing
            self.intervals.sort(key=lambda interval: (interval.effort_val, interval.start_offset))
        self.queue_draw()

    def on_draw(self, drawingarea, context: cairo.Context):
        # draw effort rectangles
        for interval in self.intervals:
            x = interval.start_offset * drawingarea.get_allocated_width() / self.max_duration
            w = interval.duration * drawingarea.get_allocated_width() / self.max_duration
            context.rectangle(x, 0, w, drawingarea.get_allocated_height())
            context.set_source_rgb(interval.color[0] / 255.0,
                                   interval.color[1] / 255.0,
                                   interval.color[2] / 255.0)
            context.fill_preserve()
            context.stroke()

        # now overdraw cadence line
        for interval in self.intervals:
            x = interval.start_offset * drawingarea.get_allocated_width() / self.max_duration
            w = interval.duration * drawingarea.get_allocated_width() / self.max_duration
            # cadence y scaling: max_y=40, min_y=130
            y = max(0, 130 - interval.cadence) * drawingarea.get_allocated_height() / (130 - 40)
            context.set_source_rgb(0, 0, 0)
            context.set_line_width(3)
            context.move_to(x, y)
            context.line_to(x + w, y)
            context.stroke()
