from argparse import ArgumentParser
import datetime
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
from gi.repository import GLib, Gtk, Pango  # noqa: E402 # need to call require_version before we can call this

gi.require_version('Gdk', '3.0')
from gi.repository import Gdk  # noqa: E402 # need to call require_version before we can call this


def load_icon(icons_to_try):
    theme = Gtk.IconTheme()
    if sys.platform == 'darwin':
        # default search path with `brew install adwaita-icon-theme` didn't work
        theme.append_search_path('/usr/local/Cellar/adwaita-icon-theme/3.34.3/share/icons/')  # TODO: Remove this??

    for icon_to_try in icons_to_try:
        try:
            pixbuf = theme.load_icon(icon_to_try, 32, 0)
        except GLib.GError:
            continue
        return pixbuf

    logging.warning("Unable to find an icon to represent a downloaded video")

    return None


def downloaded_icon():
    return load_icon(['emblem-ok-symbolic',
                      'emblem-downloads',
                      'emblem-shared'])


def downloading_icon():
    return load_icon(['emblem-synchronizing-symbolic',
                      'emblem-synchronizing'])


def format_mm_ss(ss):
    mm = ss / 60.
    ss = ss - int(mm) * 60
    return '%02u:%02u' % (mm, ss)


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

    def stop(self):
        raise NotImplementedError()


class Mp3IndexWindow(PlayerWindowInterface):
    def __init__(self,
                 config: Config,
                 label: str,
                 mp3index: Mp3Index):
        super().__init__(config, label)
        self.mp3index = mp3index
        self.player = None  # set when the main button is clicked and we start playing
        self.button.set_sensitive(self.mp3index is not None)

    def add_windows_to_stack(self, stack):
        self.stack = stack

        self.artist_label = Gtk.Label()
        self.artist_label.set_label("<artist>")
        self.title_label = Gtk.Label()
        self.title_label.set_label("<title>")
        self.time_label = Gtk.Label()
        self.time_label.set_label("<current time>")
        self.time_label.set_halign(Gtk.Align.END)  # right align
        self.duration_label = Gtk.Label()
        self.duration_label.set_label("/ <duration>")
        self.duration_label.set_halign(Gtk.Align.START)  # left align

        for (label, font_size) in ((self.artist_label, 36),
                                   (self.title_label, 48),
                                   (self.time_label, 24),
                                   (self.duration_label, 24)):
            context = label.create_pango_context()
            font_desc = context.get_font_description()
            font_desc.set_family('sans')
            font_desc.set_weight(Pango.Weight.BOLD)
            font_desc.set_size(font_size * Pango.SCALE)
            label.override_font(font_desc)

        self.back_button = Gtk.Button(label="Back")
        self.back_button.connect('clicked', self.on_back_button_clicked)

        vbox = Gtk.VBox()
        vbox.pack_start(self.artist_label, expand=True, fill=True, padding=10)
        vbox.pack_start(self.title_label, expand=True, fill=True, padding=10)
        hbox = Gtk.HBox()
        hbox.pack_start(self.time_label, expand=True, fill=True, padding=10)
        hbox.pack_start(self.duration_label, expand=True, fill=True, padding=10)
        vbox.pack_start(hbox, expand=True, fill=True, padding=10)
        vbox.pack_start(self.back_button, expand=True, fill=True, padding=10)
        stack.add_named(vbox, "mp3_info_box")

    def on_back_button_clicked(self, widget):
        self.stop()
        self.stack.set_visible_child_name("main_window_buttons")

    def on_main_button_clicked(self, widget):
        self.play_random_file()
        assert self.stack
        self.stack.set_visible_child_name("mp3_info_box")
        GLib.timeout_add_seconds(1, self.on_timer_tick)

    def on_timer_tick(self):
        if self.player:
            if self.play_started_at:
                delta = datetime.datetime.now() - self.play_started_at
                time_str = format_mm_ss(delta.seconds)
            else:
                time_str = ''
            self.time_label.set_label(time_str)

            if self.player.is_finished():
                self.play_random_file()
            return True
        else:
            return False  # don't call me again

    def play_random_file(self):
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
            self.time_label.set_label(format_mm_ss(0))
            self.duration_label.set_label('/ %s' % format_mm_ss(duration_ss))
            self.play_started_at = datetime.datetime.now()
        else:
            self.time_label.set_label('')
            self.duration_label.set_label('')
            self.play_random_file = None  # don't attempt to show time in file
        self.player = self.config.players['.mp3']
        self.player.play(mp3filename)

    def stop(self):
        if self.player:
            self.player.stop()
            self.player = None


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
        self.downloading_icon = downloading_icon()
        self.downloading_id = None  # the id of the video that we are showing is being downloaded

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

        self.main_session_index_window = Gtk.ScrolledWindow()
        self.main_session_index_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
        self.main_session_listbox = Gtk.ListBox()
        self.main_session_index_window.add(self.main_session_listbox)
        for video in self.session_feed:
            self.main_session_listbox.add(row_button(video.name, self.on_video_button_clicked, video))
        self.main_session_listbox.add(row_button("Back", self.on_back_button_clicked, None))

        stack.add_named(self.main_session_index_window, "main_session_index_window")

    def on_main_button_clicked(self, widget):
        self.update_download_icons()
        if self.downloading_id:
            GLib.timeout_add_seconds(2, self.on_check_download_complete)
        # and show the index of videos
        assert self.stack
        self.stack.set_visible_child_name("main_session_index_window")

    def on_back_button_clicked(self, widget):
        self.stack.set_visible_child_name("main_window_buttons")

    def on_check_download_complete(self):
        if self.downloading_id is None:
            return False  # don't call me again
        if self.video_cache.active_download_id != self.downloading_id:
            self.update_download_icons()
        return self.downloading_id is not None

    def on_video_button_clicked(self, widget):
        # widget is the Button (in the ListBoxRow)
        feed_item = widget.feed_item
        if feed_item:
            video_file = self.video_cache.cached_downloads.get(feed_item.id)
            if video_file:
                # play it!
                player = self.config.players[video_file.suffix]
                player.play(video_file)

    def update_download_icons(self):
        # Update the display whether files are in the cache
        index = 0
        self.downloading_id = None
        while True:
            row = self.main_session_listbox.get_row_at_index(index)
            if row is None:
                break
            if row.feed_item and self.video_cache.cached_downloads.get(row.feed_item.id):
                row.image.set_from_pixbuf(self.downloaded_icon)
            elif row.feed_item and self.video_cache.active_download_id == row.feed_item.id:
                self.downloading_id = row.feed_item.id
                row.image.set_from_pixbuf(self.downloading_icon)
            else:
                row.image.clear()
            index += 1

    def stop(self):
        pass  # TODO


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
        self.main_session_handler = MainSessionIndexWindow(self.config,
                                                           "Main session",
                                                           main_session_feed,
                                                           self.video_cache)

        # Initialise the window
        self.set_border_width(200)

        display = Gdk.Display().get_default()
        monitor = display.get_primary_monitor()
        workarea = monitor.get_workarea()
        self.set_size_request(workarea.width, workarea.height)

        self.stack = Gtk.Stack()
        self.add(self.stack)
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(1000)

        main_window_buttons = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_window_buttons.pack_start(self.warmup_handler.button, expand=True, fill=True, padding=100)
        main_window_buttons.pack_start(self.main_session_handler.button, expand=True, fill=True, padding=100)
        self.stack.add_named(main_window_buttons, "main_window_buttons")

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
    video_feed = VideoFeed.init_from_feed_url(args.session_feed_url)
    warm_up_mp3s = Mp3Index(args.config.warm_up_music_directory) if args.config.warm_up_music_directory else None
    video_cache = VideoCache(args.config, video_feed, args.update_cache)
    window = ApplicationWindow(args.config, warm_up_mp3s, video_feed, video_cache)
    window.show_all()
    Gtk.main()


if __name__ == '__main__':
    main()
