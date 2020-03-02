from argparse import ArgumentParser
import logging
import pathlib
import sys

from config import Config
from mp3index import Mp3Index
from videocache import VideoCache
from videofeed import VideoFeed, VideoFeedItem

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk  # noqa: E402 # need to call require_version before we can call this

# gi.require_version('GdkX11', '3.0')
# from gi.repository import GdkX11


def downloaded_icon():
    theme = Gtk.IconTheme()
    if sys.platform == 'darwin':
        # default search path with `brew install adwaita-icon-theme` didn't work
        theme.append_search_path('/usr/local/Cellar/adwaita-icon-theme/3.34.3/share/icons/')  # TODO: Remove this??

    for icon_to_try in ('emblem-ok-symbolic',
                        'emblem-downloads',
                        'emblem-shared'):
        try:
            pixbuf = theme.load_icon(icon_to_try, 32, 0)
        except GLib.GError:
            continue
        return pixbuf

    logging.warning("Unable to find an icon to represent a downloaded video")

    return None


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
        self.mp3index = mp3index
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

        self.downloaded_icon = downloaded_icon()

        main_window_buttons = self._init_main_window_buttons()
        self.main_session_listbox = self._init_main_session_index_window()

        self.stack = Gtk.Stack()
        self.add(self.stack)
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(1000)
        self.stack.add_named(main_window_buttons, "main_window_buttons")
        self.stack.add_named(self.main_session_listbox, "main_session_index")

    def _init_main_window_buttons(self):
        """
        Initialise the buttons on the main window
        """
        self.warm_up_button = Gtk.Button(label="Warm up")
        self.warm_up_button.connect("clicked", self.on_warm_up_button_clicked)
        self.warm_up_button.set_sensitive(self.mp3index is not None)

        self.main_session_button = Gtk.Button(label="Main session")
        self.main_session_button.connect("clicked", self.on_main_session_clicked)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.pack_start(self.warm_up_button, expand=True, fill=True, padding=100)
        vbox.pack_start(self.main_session_button, expand=True, fill=True, padding=100)

        return vbox

    def _init_main_session_index_window(self):
        """
        Initialise the window showing the main session video index
        """

        def row_button(label, handler, feed_item: VideoFeedItem):
            button = Gtk.Button(label=label)
            button.connect('clicked', handler)
            button.feed_item = feed_item
            button.set_can_focus(False)
            overlay = Gtk.Overlay()
            overlay.add(button)
            image = Gtk.Image()
            overlay.add_overlay(image)
            overlay.set_overlay_pass_through(image, True)
            # This next method is deprecated, but it actually works
            # The documentation shows a mismatch: Gtk.Image has
            # xalign / yalign, yet the Overlay looks at the
            # halign / valign parameters
            image.set_alignment(Gtk.Align.END, Gtk.Align.START)
            # the actual image is set when we show the window,
            # so that it reacts as the cache populates
            row = Gtk.ListBoxRow()
            row.feed_item = feed_item
            row.image = image
            row.add(overlay)
            row.connect('activate', handler)
            return row

        listbox = Gtk.ListBox()
        for video in self.main_session_feed:
            listbox.add(row_button(video.name, self.on_video_button_clicked, video))
        listbox.add(row_button("Back", self.on_back_button_clicked, None))
        return listbox

    def on_back_button_clicked(self, widget):
        self.stack.set_visible_child_name("main_window_buttons")

    def on_key_press(self, widget, event):
        if ((event.state & self.quit_key_accel_mods) == self.quit_key_accel_mods) and \
           (event.keyval == self.quit_key_accel_keyval):
            Gtk.main_quit()

    def on_main_session_clicked(self, widget):
        # Update the display whether files are in the cache
        index = 0
        while True:
            row = self.main_session_listbox.get_row_at_index(index)
            if row is None:
                break
            if row.feed_item and self.video_cache.cached_downloads.get(row.feed_item.id):
                row.image.set_from_pixbuf(self.downloaded_icon)
            else:
                row.image.clear()
            index += 1
        # and show the index of videos
        self.stack.set_visible_child_name("main_session_index")

    def on_quit(self, *args):
        self.video_cache.stop_download()
        Gtk.main_quit()

    def on_video_button_clicked(self, widget):
        # widget is the Button (in the ListBoxRow)
        feed_item = widget.feed_item
        if feed_item:
            video_file = self.video_cache.cached_downloads.get(feed_item.id)
            if video_file:
                # play it!
                player = self.config.players[video_file.suffix]
                player.play(video_file)

    def on_warm_up_button_clicked(self, widget):
        pass


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
    default_config = pathlib.Path.home() / '.picaverc'
    default_feed = pathlib.Path(__file__).parent / '..' / 'feed' / 'index.json'
    parser.set_defaults(config=default_config,
                        session_feed_url=default_feed.resolve().as_uri(),
                        update_cache=True)
    args = parser.parse_args()
    if args.config.exists():
        args.config = Config(args.config)
    else:
        logging.warnign("Configuration file not found")
        args.config = Config()
    return args


def main():
    args = parse_args()
    video_feed = VideoFeed.init_from_feed_url(args.session_feed_url)
    warm_up_mp3s = Mp3Index(args.config.warm_up_music_directory) if args.config.warm_up_music_directory else None
    video_cache = VideoCache(args.config, video_feed, args.update_cache)
    window = ApplicationWindow(args.config, warm_up_mp3s, video_feed, video_cache)
    window.show_all()
    Gtk.main()


if __name__ == '__main__':
    main()
