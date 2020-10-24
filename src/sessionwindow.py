from config import Config
from intervalwindow import IntervalWindow

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402 # need to call require_version before we can call this


class SessionWindow:
    def __init__(self, config: Config, feed_url: str):
        self.video_window = None
        self.interval_window = IntervalWindow(config, feed_url)

        video_layout = Gtk.HBox()
        # TODO: video player
        video_layout.pack_start(self.interval_window, expand=True, fill=True, padding=0)  # TODO: Proper padding
        self.interval_window.set_margin_start(1500)  # pad on left side only

        self.window_for_stack = video_layout

    def play(self, video_id):
        # TODO: video play
        self.interval_window.play(video_id)

    def play_pause(self):
        # TODO: video pause
        self.interval_window.play_pause()
