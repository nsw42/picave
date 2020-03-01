from argparse import ArgumentParser
import pathlib
import sys

from config import Config
from videocache import VideoCache
from videofeed import VideoFeed

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402 # need to call require_version before we can call this

# gi.require_version('GdkX11', '3.0')
# from gi.repository import GdkX11


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

    def __init__(self, config: Config, main_session_feed: VideoFeed, video_cache: VideoCache):
        self.config = config
        self.main_session_feed = main_session_feed
        self.video_cache = video_cache
        Gtk.Window.__init__(self, title="Pi Cave")
        self.connect("destroy", self.on_quit)
        self.connect("delete-event", self.on_quit)
        self._init_main_window()

    def _init_main_window(self):
        """
        Initialise the top-level window
        """
        self.set_border_width(200)

        self.quit_key_accel_keyval, self.quit_key_accel_mods = Gtk.accelerator_parse('<Primary>Q')
        self.connect('key-press-event', self.on_key_press)

        self.set_size_request(1920, 1000)

        main_window_buttons = self._init_main_window_buttons()
        main_session_index_window = self._init_main_session_index_window()

        self.stack = Gtk.Stack()
        self.add(self.stack)
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(1000)
        self.stack.add_named(main_window_buttons, "main_window_buttons")
        self.stack.add_named(main_session_index_window, "main_session_index")

    def _init_main_window_buttons(self):
        """
        Initialise the buttons on the main window
        """
        self.main_session_button = Gtk.Button(label="Main session")
        self.main_session_button.connect("clicked", self.on_main_session_clicked)

        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.vbox.pack_start(self.main_session_button, expand=True, fill=True, padding=250)

        return self.vbox

    def _init_main_session_index_window(self):
        """
        Initialise the window showing the main session video index
        """
        def row_button(label, handler, filename):
            button = Gtk.Button(label=label)
            button.connect('clicked', handler)
            button.set_can_focus(False)
            button.video_file = filename
            row = Gtk.ListBoxRow()
            row.add(button)
            row.connect('activate', handler)
            return row

        listbox = Gtk.ListBox()
        for video in self.main_session_feed:
            listbox.add(row_button(video.name, self.on_video_button_clicked, video.url))
        listbox.add(row_button("Back", self.on_back_button_clicked, None))
        return listbox

    def on_back_button_clicked(self, widget):
        self.stack.set_visible_child_name("main_window_buttons")

    def on_key_press(self, widget, event):
        if ((event.state & self.quit_key_accel_mods) == self.quit_key_accel_mods) and \
           (event.keyval == self.quit_key_accel_keyval):
            Gtk.main_quit()

    def on_main_session_clicked(self, widget):
        self.stack.set_visible_child_name("main_session_index")

    def on_quit(self, *args):
        self.video_cache.stop_download()
        Gtk.main_quit()

    def on_video_button_clicked(self, widget):
        print(widget.video_file)
        # self.config.play()


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('-c', '--config', metavar='FILENAME', action='store', type=pathlib.Path,
                        help="Load configuration from FILENAME. "
                             "Default %(default)s")
    parser.add_argument('--session-feed-url', metavar='URL', action='store',
                        help="Specify where to find the session video index feed. "
                             "Default %(default)s")
    default_config = pathlib.Path.home() / '.picaverc'
    default_feed = pathlib.Path(__file__).parent / '..' / 'feed' / 'index.json'
    parser.set_defaults(config=default_config,
                        session_feed_url=default_feed.resolve().as_uri())
    args = parser.parse_args()
    if args.config.exists():
        args.config = Config(args.config)
    else:
        print("WARNING: Configuration file not found", file=sys.stderr)
        args.config = Config()
    return args


def main():
    args = parse_args()
    video_feed = VideoFeed.init_from_feed_url(args.session_feed_url)
    video_cache = VideoCache(args.config, video_feed)
    window = ApplicationWindow(args.config, video_feed, video_cache)
    window.show_all()
    Gtk.main()


if __name__ == '__main__':
    main()
