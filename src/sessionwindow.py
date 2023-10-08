# pylint: disable=wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk  # noqa: E402

from config import Config  # noqa: E402
from intervalwidget import IntervalWidget  # noqa: E402
from playerwindowinterface import PlayerWindowInterface  # noqa: E402
# pylint: enable=wrong-import-position


class SessionWindow(PlayerWindowInterface):
    def __init__(self,
                 config: Config,
                 label: str,
                 feed_url: str):
        super().__init__(config, label)
        self.video_area = Gtk.DrawingArea()
        self.video_file = None
        self.video_id = None
        self.playing = False
        self.realized = False
        self.size_known = False

        self.interval_window = IntervalWidget(config, feed_url)
        self.interval_window.set_size_request(256, -1)

        self.video_layout = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.video_layout.set_homogeneous(False)
        self.video_layout.pack_start(self.video_area, expand=True, fill=True, padding=0)
        self.video_layout.pack_start(self.interval_window, expand=False, fill=False, padding=0)

        self.video_area.connect("draw", self.on_draw)
        self.video_area.connect("realize", self.on_realized)
        self.video_area.connect("size-allocate", self.on_size_changed)

    def add_windows_to_stack(self, stack, window_name_to_handler):
        self.stack = stack
        session_window_name = "session_window"
        stack.add_named(self.video_layout, session_window_name)
        window_name_to_handler[session_window_name] = self

    def have_all_prerequisites_for_playing(self):
        return (self.video_file is not None) and (self.realized) and (self.size_known)

    def on_draw(self, _widget, context, _data=None):
        context.set_source_rgb(0, 0, 0)
        context.paint()

    def on_realized(self, _widget, _data=None):
        self.realized = True
        if self.have_all_prerequisites_for_playing():
            self.start_playing()

    def on_size_changed(self, _widget, allocation):
        # This might be the final event allowing us to actually start playback,
        # or it might be a size change when we're already playing
        self.size_known = True
        if self.player:
            self.player.window_size_changed(allocation)
        else:
            if self.have_all_prerequisites_for_playing():
                self.start_playing()

    def play(self, video_file, video_id):
        self.playing = True
        self.video_file = video_file
        self.video_id = video_id
        if self.have_all_prerequisites_for_playing():
            self.start_playing()

    def start_playing(self):
        # pre-requisites for playing a video:
        # * what file to play (via play())
        # * what window to play into (via on_realized())
        # * what size the window is (via on_size_changed())
        # play() gets called before on_realized() for the first video;
        # but on_realized() is only called once, whereas play() can be
        # called multiple times.
        # For the first video, on_realized() is soon followed by
        # on_size_changed(), which is where we then set the video scaling;
        # on_size_changed() is not expected for later videos.
        assert self.player is None
        self.player = self.config.players[self.video_file.suffix]
        self.player.play(self.video_file, self.video_area)
        self.interval_window.play(self.video_id)
        GLib.timeout_add_seconds(1, self.monitor_for_end_of_video)

    def play_pause(self):
        assert self.player
        self.player.play_pause()
        self.interval_window.play_pause()

    def stop(self):
        if self.player:
            self.player.stop()
        self.player = None
        self.video_file = None
        self.playing = False

    def monitor_for_end_of_video(self):
        if self.player is None:
            return False  # we've already taken appropriate actions

        still_playing = not self.player.is_finished()

        if not still_playing:
            self.stop()
            assert self.stack
            self.stack.set_visible_child_name("main_session_index_window")
        return still_playing

    def on_main_button_clicked(self, widget):
        # This method only exists for interface compatibility.
        # PlayerWindowInterface inherits from StackWindowWithButtonInterface,
        # but SessionWindow is not a StackWindowWithButton.
        pass
