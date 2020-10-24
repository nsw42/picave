import ctypes
import sys

import vlc

from config import Config
from intervalwindow import IntervalWindow
from windowinterface import PlayerWindowInterface

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk  # noqa: E402 # need to call require_version before we can call this


def get_window_handle_helper(widget):
    # https://gitlab.gnome.org/GNOME/pygobject/issues/112
    if sys.platform == "darwin":
        return get_window_handle_helper_darwin(widget)
    else:
        return widget.get_window().get_xid()


def get_window_handle_helper_darwin(widget):
    window = widget.get_property('window')
    ctypes.pythonapi.PyCapsule_GetPointer.restype = ctypes.c_void_p
    ctypes.pythonapi.PyCapsule_GetPointer.argtypes = [ctypes.py_object]
    gpointer = ctypes.pythonapi.PyCapsule_GetPointer(window.__gpointer__, None)
    libgdk = ctypes.CDLL("libgdk-3.dylib")
    libgdk.gdk_quartz_window_get_nsview.restype = ctypes.c_void_p
    libgdk.gdk_quartz_window_get_nsview.argtypes = [ctypes.c_void_p]
    handle = libgdk.gdk_quartz_window_get_nsview(gpointer)
    return handle


class SessionWindow(PlayerWindowInterface):
    def __init__(self,
                 config: Config,
                 label: str,
                 feed_url: str):
        super().__init__(config, label)
        self.video_area = Gtk.DrawingArea()
        self.video_area.set_size_request(1500, 0)  # set the width, allow height to sort itself out
        self.video_area.connect("realize", self.on_realized)
        self.video_player = None
        self.video_file = None
        self.playing = False

        self.interval_window = IntervalWindow(config, feed_url)

        self.video_layout = Gtk.HBox()
        self.video_layout.pack_start(self.video_area, expand=True, fill=True, padding=0)
        self.video_layout.pack_start(self.interval_window, expand=True, fill=True, padding=0)  # TODO: Proper padding

    def add_windows_to_stack(self, stack, window_name_to_handler):
        session_window_name = "session_window"
        stack.add_named(self.video_layout, session_window_name)
        window_name_to_handler[session_window_name] = self.video_layout

    def on_realized(self, widget, data=None):
        assert self.video_file  # play() must be called before this window is realised
        assert self.playing
        self.vlcInstance = vlc.Instance("--no-xlib")
        self.video_player = self.vlcInstance.media_player_new()
        win_id = get_window_handle_helper(widget)
        self.video_player.set_xwindow(win_id)
        self.video_player.set_mrl(self.video_file.as_uri())
        # TODO reinstate - self.video_player.play()
        # self.playback_button.set_image(self.pause_image)
        # self.is_player_active = True

    def play(self, video_file, video_id):
        self.playing = True
        self.video_file = video_file
        self.interval_window.play(video_id)
        GLib.timeout_add_seconds(1, self.monitor_for_end_of_video)

    def play_pause(self):
        assert self.video_player
        if self.playing:
            self.video_player.pause()
        else:
            self.video_player.play()
        self.playing = not self.playing
        self.interval_window.play_pause()

    def stop(self):
        if self.video_player:
            self.video_player.stop()

    def monitor_for_end_of_video(self):
        if self.player is None:
            return False  # we've already taken appropriate actions
        elif self.player.is_finished():
            still_playing = False
        else:
            still_playing = True

        if not still_playing:
            self.player = None
            assert self.stack
            self.stack.set_visible_child_name("main_session_index_window")
        return still_playing
