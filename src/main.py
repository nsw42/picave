from argparse import ArgumentParser
import logging
import pathlib
import sys
import subprocess
import time

from config import Config
from mainwindow import MainButtonWindow
from mp3index import Mp3Index
from mp3window import Mp3Window
import osmc
from videocache import VideoCache
from videofeed import VideoFeed
from videoindexwindow import VideoIndexWindow

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402 # need to call require_version before we can call this

gi.require_version('Gdk', '3.0')
from gi.repository import Gdk  # noqa: E402 # need to call require_version before we can call this

gi.require_version('GLib', '2.0')
from gi.repository import GLib  # noqa: E402 # need to call require_version before we can call this


class ExitDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(title="Really quit?",
                         parent=parent,
                         flags=0)
        self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        self.add_button("Quit", Gtk.ResponseType.OK)
        self.add_button("Shutdown", Gtk.ResponseType.CLOSE)
        self.set_default_size(150, 100)

        self.show_all()


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

        self.key_table = []
        for (keyname, handler) in [
            ('<Primary>Q', self.on_quit),
            ('Escape', self.on_show_home),  # OSMC 'Home' button
            ('c', self.on_show_index),  # OSMC 'index' button
            ('P', self.on_play_pause),  # TODO: Remove me
        ]:
            keyval, mods = Gtk.accelerator_parse(keyname)
            self.key_table.append((keyval, mods, handler))
        self.connect('key-press-event', self.on_key_press)

        self.warmup_handler = Mp3Window(self.config, "Warm up", mp3index)
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

        self.quit_menu = Gtk.Menu()
        self.quit_menu.append(Gtk.MenuItem.new_with_label("Cancel"))
        self.quit_menu.append(Gtk.MenuItem.new_with_label("Quit"))
        self.quit_menu.append(Gtk.MenuItem.new_with_label("Shutdown"))

        self.osmc = osmc.look_for_osmc()
        if self.osmc:
            logging.debug("OSMC enabled")
            self.osmc_handlers = {
                osmc.KEY_BACK: self.on_back_button,
                osmc.KEY_PLAYPAUSE: self.on_play_pause,
            }
            GLib.timeout_add(50, self.check_osmc_events)  # 50ms = 1/20s

    def check_osmc_events(self):
        event = self.osmc.poll_for_key_event()
        if event:
            logging.debug("OSMC %u", event.key)
            handler = self.osmc_handlers.get(event.key)
            if handler:
                handler()
        return True  # keep looking for OSMC events

    def on_key_press(self, widget, event):
        logging.debug('Key: hw: %s / state: %s / keyval: %s' % (event.hardware_keycode, event.state, event.keyval))
        for (keyval, mods, handler) in self.key_table:
            if ((event.state & mods) == mods) and (event.keyval == keyval):
                handler()
                return True  # we've handled the event
        return False

    def on_back_button(self):
        if self.stack.get_visible_child_name() == "main_window_buttons":
            dialog = ExitDialog(self)
            response = dialog.run()
            dialog.destroy()

            logging.debug("Response %u", response)

            if response == Gtk.ResponseType.CANCEL:
                # No action required
                pass
            elif response == Gtk.ResponseType.OK:
                self.on_quit()
            elif response == Gtk.ResponseType.CLOSE:
                self.on_shutdown()
        else:
            self.on_show_home()

    def on_play_pause(self):
        visible_child = self.stack.get_visible_child_name()
        logging.debug("on_play_pause: visible child %s", visible_child)
        # TODO: Checking the child name is a layering violation
        if visible_child == 'main_window_buttons':
            logging.debug('Ignoring play/pause on main window')
        elif visible_child == 'mp3_info_box':
            self.warmup_handler.play_pause()
        elif visible_child == 'interval_window':
            self.main_session_handler.play_pause()

    def on_show_home(self):
        self.stop_playing()
        self.stack.set_visible_child_name("main_window_buttons")

    def on_show_index(self):
        self.stop_playing()
        self.main_session_handler.on_main_button_clicked(None)

    def on_quit(self, *args):
        self.stop_playing()
        self.video_cache.stop_download()
        Gtk.main_quit()

    def on_shutdown(self, *args):
        self.on_quit()
        subprocess.run(['sudo', 'shutdown', '-h', '+1'])  # give a minute to interrupt (shutdown -c)

    def stop_playing(self):
        self.warmup_handler.stop()
        self.main_session_handler.stop()


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
    parser.add_argument('--wait-for-media', action='store_true',
                        help="Wait until the video cache directory is present. "
                             "Default behaviour is to report an error and exit.")
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


def safe_check_dir(dirpath):
    try:
        if dirpath.is_dir():
            return True
        return False
    except PermissionError:
        logging.warning("%s PermissionError" % dirpath)
        return False


def check_media(args):
    if args.wait_for_media:
        while not safe_check_dir(args.config.video_cache_directory):
            logging.warning("%s does not exist. Waiting." % args.config.video_cache_directory)
            time.sleep(1)

        if args.config.warm_up_music_directory:
            while not safe_check_dir(args.config.warm_up_music_directory):
                logging.warning("%s does not exist. Waiting." % args.config.warm_up_music_directory)
                time.sleep(1)
    else:
        if not safe_check_dir(args.config.video_cache_directory):
            sys.exit("%s does not exist" % args.config.video_cache_directory)

        if args.config.warm_up_music_directory:
            if not safe_check_dir(args.config.warm_up_music_directory):
                logging.warning('Warm up music directory does not exist or is not a directory')
                args.config.warm_up_music_directory = None


def main():
    args = parse_args()

    check_media(args)  # will sys.exit() if media do not exist

    video_feed = VideoFeed(args.session_feed_url)
    warm_up_mp3s = Mp3Index(args.config.warm_up_music_directory) if args.config.warm_up_music_directory else None
    video_cache = VideoCache(args.config, video_feed, args.update_cache)
    window = ApplicationWindow(args.config, warm_up_mp3s, video_feed, video_cache)
    window.show_all()
    Gtk.main()


if __name__ == '__main__':
    main()
