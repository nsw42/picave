from argparse import ArgumentParser
import logging
import pathlib

from config import Config
from mainwindow import MainButtonWindow
from mp3index import Mp3Index
from mp3window import Mp3IndexWindow
from videocache import VideoCache
from videofeed import VideoFeed
from videoindexwindow import VideoIndexWindow

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402 # need to call require_version before we can call this

gi.require_version('Gdk', '3.0')
from gi.repository import Gdk  # noqa: E402 # need to call require_version before we can call this


class ApplicationWindow(Gtk.ApplicationWindow):
    """
    Main application window.
    Creates and manages the following window hierarchy:
     * main window
       * Stack
         * main window buttons
           * Button("Main session") (clicking shows the main session video index)
         * main session index (a listbox of videos)
    """

    def __init__(self,
                 config: Config,
                 mp3index: Mp3Index,
                 main_session_feed: VideoFeed,
                 video_cache: VideoCache):
        self.config = config
        self.main_session_feed = main_session_feed
        self.video_cache = video_cache
        Gtk.Window.__init__(self, title="Pi Cave")
        self.connect("destroy", self.on_quit)
        self.connect("delete-event", self.on_quit)

        self.quit_key_accel_keyval, self.quit_key_accel_mods = Gtk.accelerator_parse('<Primary>Q')
        self.connect('key-press-event', self.on_key_press)

        self.warmup_handler = Mp3IndexWindow(self.config, "Warm up", mp3index)
        self.main_session_handler = VideoIndexWindow(self.config,
                                                     "Main session",
                                                     main_session_feed,
                                                     self.video_cache)
        self.main_buttons = MainButtonWindow([self.warmup_handler,
                                              self.main_session_handler])

        display = Gdk.Display().get_default()
        monitor = display.get_primary_monitor()
        workarea = monitor.get_workarea()
        self.set_size_request(workarea.width, workarea.height)

        self.stack = Gtk.Stack()
        self.add(self.stack)
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(1000)

        self.main_buttons.add_windows_to_stack(self.stack)
        self.warmup_handler.add_windows_to_stack(self.stack)
        self.main_session_handler.add_windows_to_stack(self.stack)

        self.stack.set_visible_child_name("main_window_buttons")

    def on_key_press(self, widget, event):
        if ((event.state & self.quit_key_accel_mods) == self.quit_key_accel_mods) and \
           (event.keyval == self.quit_key_accel_keyval):
            self.on_quit()

    def on_quit(self, *args):
        self.video_cache.stop_download()
        self.warmup_handler.stop()
        self.main_session_handler.stop()
        Gtk.main_quit()


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('-c', '--config', metavar='FILENAME', action='store', type=pathlib.Path,
                        help="Load configuration from FILENAME. "
                             "Default %(default)s")
    parser.add_argument('--session-feed-url', metavar='URL', action='store',
                        help="Specify where to find the session video index feed. "
                             "Default %(default)s")
    parser.add_argument('--no-cache', action='store_false', dest='update_cache',
                        help="Disable populating the cache")
    parser.add_argument('--debug', action='store_true',
                        help="Show debug information")
    default_config = pathlib.Path.home() / '.picaverc'
    default_feed = pathlib.Path(__file__).parent / '..' / 'feed' / 'index.json'
    parser.set_defaults(config=default_config,
                        debug=False,
                        session_feed_url=default_feed.resolve().as_uri(),
                        update_cache=True)
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    if args.config.exists():
        args.config = Config(args.config)
    else:
        logging.warning("Configuration file not found")
        args.config = Config()
    return args


def main():
    args = parse_args()
    video_feed = VideoFeed(args.session_feed_url)
    warm_up_mp3s = Mp3Index(args.config.warm_up_music_directory) if args.config.warm_up_music_directory else None
    video_cache = VideoCache(args.config, video_feed, args.update_cache)
    window = ApplicationWindow(args.config, warm_up_mp3s, video_feed, video_cache)
    window.show_all()
    Gtk.main()


if __name__ == '__main__':
    main()
