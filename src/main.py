from argparse import ArgumentParser
import logging
import pathlib
import sys

import mutagen

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


class PlayerWindowInterface(object):
    def __init__(self,
                 config: Config,
                 label: str):
        """
        The constructor for any kind of player window does the following:
         * create a button, which is to be shown on the front page
         * create one or more windows, to show the player
         * set up the click handler for that button to switch the stack to the appropriate window
        """
        self.stack = None  # initialised during add_windows_to_stack
        self.config = config
        self.button = Gtk.Button(label=label)
        self.button.connect("clicked", self.on_main_button_clicked)

    def add_windows_to_stack(self, stack):
        raise NotImplementedError()

    def on_main_button_clicked(self, widget):
        raise NotImplementedError()  # to be overridden by the relevant player window class


class Mp3IndexWindow(PlayerWindowInterface):
    def __init__(self,
                 config: Config,
                 label: str,
                 mp3index: Mp3Index):
        super().__init__(config, label)
        self.mp3index = mp3index
        self.button.set_sensitive(self.mp3index is not None)

    def add_windows_to_stack(self, stack):
        self.stack = stack

        self.artist_label = Gtk.Label()
        self.artist_label.set_label("<artist>")
        self.title_label = Gtk.Label()
        self.title_label.set_label("<title>")
        self.duration_label = Gtk.Label()
        self.duration_label.set_label("<duration>")

        self.back_button = Gtk.Button(label="Back")
        self.back_button.connect('clicked', self.on_back_button_clicked)

        box = Gtk.VBox()
        box.pack_start(self.artist_label, expand=True, fill=True, padding=10)
        box.pack_start(self.title_label, expand=True, fill=True, padding=10)
        box.pack_start(self.duration_label, expand=True, fill=True, padding=10)
        box.pack_start(self.back_button, expand=True, fill=True, padding=10)
        stack.add_named(box, "mp3_info_box")

    def on_back_button_clicked(self, widget):
        self.stack.set_visible_child_name("main_window_buttons")

    def on_main_button_clicked(self, widget):
        mp3filename = self.mp3index.random_file()
        reader = mutagen.File(mp3filename)
        artist = reader.tags.get('TPE1')
        if artist:
            self.artist_label.set_label('\n'.join(artist.text))
        title = reader.tags.get('TIT2')
        if title:
            self.title_label.set_label('\n'.join(title.text))
        duration_ss = reader.info.length
        if duration_ss:
            mm = duration_ss / 60.
            ss = duration_ss - int(mm) * 60
            self.duration_label.set_label('%02u:%02u' % (mm, ss))
        player = self.config.players['.mp3']
        player.play(mp3filename)
        assert self.stack
        self.stack.set_visible_child_name("mp3_info_box")


class MainSessionIndexWindow(PlayerWindowInterface):
    def __init__(self,
                 config: Config,
                 label: str,
                 session_feed: VideoFeed,
                 video_cache: VideoCache):
        super().__init__(config, label)
        self.session_feed = session_feed
        self.video_cache = video_cache

        self.downloaded_icon = downloaded_icon()

    def add_windows_to_stack(self, stack):
        self.stack = stack

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

        self.main_session_listbox = Gtk.ListBox()
        for video in self.session_feed:
            self.main_session_listbox.add(row_button(video.name, self.on_video_button_clicked, video))
        self.main_session_listbox.add(row_button("Back", self.on_back_button_clicked, None))

        stack.add_named(self.main_session_listbox, "main_session_listbox")

    def on_main_button_clicked(self, widget):
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
        assert self.stack
        self.stack.set_visible_child_name("main_session_listbox")

    def on_back_button_clicked(self, widget):
        self.stack.set_visible_child_name("main_window_buttons")

    def on_video_button_clicked(self, widget):
        # widget is the Button (in the ListBoxRow)
        feed_item = widget.feed_item
        if feed_item:
            video_file = self.video_cache.cached_downloads.get(feed_item.id)
            if video_file:
                # play it!
                player = self.config.players[video_file.suffix]
                player.play(video_file)


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

        warmup_handler = Mp3IndexWindow(self.config, "Warm up", mp3index)
        main_session_handler = MainSessionIndexWindow(self.config, "Main session", main_session_feed, self.video_cache)

        # Initialise the window
        self.set_border_width(200)

        self.set_size_request(1920, 1000)

        self.stack = Gtk.Stack()
        self.add(self.stack)
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(1000)

        main_window_buttons = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_window_buttons.pack_start(warmup_handler.button, expand=True, fill=True, padding=100)
        main_window_buttons.pack_start(main_session_handler.button, expand=True, fill=True, padding=100)
        self.stack.add_named(main_window_buttons, "main_window_buttons")

        warmup_handler.add_windows_to_stack(self.stack)
        main_session_handler.add_windows_to_stack(self.stack)

        self.stack.set_visible_child_name("main_window_buttons")

    def on_key_press(self, widget, event):
        if ((event.state & self.quit_key_accel_mods) == self.quit_key_accel_mods) and \
           (event.keyval == self.quit_key_accel_keyval):
            self.on_quit()

    def on_quit(self, *args):
        self.video_cache.stop_download()
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
    video_feed = VideoFeed.init_from_feed_url(args.session_feed_url)
    warm_up_mp3s = Mp3Index(args.config.warm_up_music_directory) if args.config.warm_up_music_directory else None
    video_cache = VideoCache(args.config, video_feed, args.update_cache)
    window = ApplicationWindow(args.config, warm_up_mp3s, video_feed, video_cache)
    window.show_all()
    Gtk.main()


if __name__ == '__main__':
    main()
