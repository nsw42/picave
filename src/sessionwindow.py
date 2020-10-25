import ctypes
import json
import logging
import subprocess
import sys

import vlc

from config import Config
from intervalwindow import IntervalWindow
from windowinterface import PlayerWindowInterface

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, GLib, Gtk  # noqa: E402 # need to call require_version before we can call this


def get_video_width(filepath):
    result = subprocess.run(['ffprobe', '-v', 'error', '-print_format', 'json', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', str(filepath)],
                            capture_output=True, text=True)
    result = json.loads(result.stdout)
    return result['streams'][0]['width']


class SessionWindow(PlayerWindowInterface):
    def __init__(self,
                 config: Config,
                 label: str,
                 feed_url: str):
        super().__init__(config, label)
        self.video_area = Gtk.DrawingArea()
        self.video_player = None
        self.video_file = None
        self.video_file_width = None  # The natural size of the video
        self.playing = False
        self.realized = False
        self.size_known = False

        self.interval_window = IntervalWindow(config, feed_url)
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
        window_name_to_handler[session_window_name] = self.video_layout

    def on_draw(self, widget, context, data=None):
        context.set_source_rgb(0, 0, 0)
        context.paint()

    def on_realized(self, widget, data=None):
        assert self.video_file  # play() must be called before this window is realised
        assert self.playing
        self.realized = True
        self.play_when_realized()

    def on_size_changed(self, widget, allocation):
        assert self.video_file_width
        if allocation.width > self.video_file_width:
            # Don't attempt to scale up: the R-Pi isn't up to it
            self.video_player.video_set_scale(1.0)
        else:
            # automatically scale down to fit the window
            self.video_player.video_set_scale(0.0)
        self.size_known = True

    def set_player_window(self):
        logging.debug("set_player_window")
        if sys.platform == 'win32':
            raise NotImplementedError()
        elif sys.platform == 'darwin':
            self.set_player_window_darwin()
        else:
            self.set_player_window_x11()

    def set_player_window_darwin(self):
        # https://gitlab.gnome.org/GNOME/pygobject/issues/112
        # and https://www.mail-archive.com/vlc-commits@videolan.org/msg55659.html
        # and https://github.com/oaubert/python-vlc/blob/master/examples/gtkvlc.py
        window = self.video_area.get_window()

        getpointer = ctypes.pythonapi.PyCapsule_GetPointer
        getpointer.restype = ctypes.c_void_p
        getpointer.argtypes = [ctypes.py_object]
        pointer = getpointer(window.__gpointer__, None)

        libgdk = ctypes.CDLL("libgdk-3.dylib")
        get_nsview = libgdk.gdk_quartz_window_get_nsview
        get_nsview.restype = ctypes.c_void_p
        get_nsview.argtypes = [ctypes.c_void_p]
        handle = get_nsview(pointer)

        self.video_player.set_nsobject(handle)

    def set_player_window_x11(self):
        win_id = self.video_area.get_window().get_xid()
        self.video_player.set_xwindow(win_id)

    def play(self, video_file, video_id):
        self.playing = True
        self.video_file = video_file
        self.video_file_width = get_video_width(video_file)
        self.interval_window.play(video_id)
        GLib.timeout_add_seconds(1, self.monitor_for_end_of_video)
        if self.realized:
            self.play_when_realized()

    def play_when_realized(self):
        # pre-requisites for playing a video:
        # * what file to play (via play())
        # * what window to play into (via on_realized())
        # play() gets called before on_realized() for the first video;
        # but on_realized() is only called once, whereas play() can be
        # called multiple times.
        # For the first video, on_realized() is soon followed by
        # on_size_changed(), which is where we then set the video scaling;
        # on_size_changed() is not expected for later videos.
        self.vlcInstance = vlc.Instance("--no-xlib")
        self.video_player = self.vlcInstance.media_player_new()
        self.video_player.set_mrl(self.video_file.as_uri())
        self.video_player.play()
        self.set_player_window()
        if self.size_known:
            # this is the 2nd (or later) video. Fake up a size event to
            # set the video scaling.
            self.on_size_changed(self.video_area, self.video_area.get_allocation())

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
            self.video_player = None
            self.vlcInstance = None
        self.video_file = None
        self.playing = False

    def monitor_for_end_of_video(self):
        if self.video_player is None:
            return False  # we've already taken appropriate actions

        logging.debug("monitor_for_end_of_video: %f", self.video_player.get_position())
        if self.video_player.get_state() == vlc.State.Ended:
            still_playing = False
        else:
            still_playing = True

        if not still_playing:
            self.stop()
            assert self.stack
            self.stack.set_visible_child_name("main_session_index_window")
        return still_playing
