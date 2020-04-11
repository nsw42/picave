from config import Config
from sessionview import SessionView

import cairo


class SessionPreview(SessionView):
    def __init__(self, config: Config, feed_url: str):
        super().__init__(config, feed_url)
        self.intervals = []
        self.max_duration = 1
        self.connect("draw", self.on_draw)

    def show(self, video_id):
        self.intervals = self.read_intervals(video_id)
        if self.intervals:
            self.max_duration = self.intervals[-1].start_offset.seconds + self.intervals[-1].duration
            # intervals are returned in chronological order, but sort them
            # into desired order for drawing
            self.intervals.sort(key=lambda interval: (interval.effort_val, interval.start_offset))
        self.queue_draw()

    def on_draw(self, drawingarea, context: cairo.Context):
        for interval in self.intervals:
            x = interval.start_offset.seconds * drawingarea.get_allocated_width() / self.max_duration
            w = interval.duration * drawingarea.get_allocated_width() / self.max_duration
            context.rectangle(x, 0, w, drawingarea.get_allocated_height())
            context.set_source_rgb(interval.color[0] / 255.0,
                                   interval.color[1] / 255.0,
                                   interval.color[2] / 255.0)
            context.fill_preserve()
            context.stroke()
