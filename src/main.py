from argparse import ArgumentParser
import logging
import pathlib
import sys
import time

from applicationwindow import ApplicationWindow
import config
from mp3index import Mp3Index
from profilechooserwindow import ProfileChooserWindow
from videocache import VideoCache
from videofeed import VideoFeed

import gi
gi.require_versions({
    'Gtk': '3.0',
})
from gi.repository import Gio, Gtk  # noqa: E402 # need to call require_version before we can call this


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
    parser.add_argument('--show-profile-chooser', action='store_true',
                        help="Show the profile selection window instead of loading from the "
                             "specified configuration file")
    parser.add_argument('--delay-shutdown', action='store_true',
                        help="Wait for a minute before actually shutting down")
    parser.add_argument('--hide-mouse-pointer', action='store_true',
                        help="Hide the mouse pointer over the main window")
    parser.add_argument('--full-screen', action='store_true',
                        help="Go full screen when starting")
    parser.add_argument('--debug', action='store_true',
                        help="Show debug information")
    default_config = config.default_config_path()
    default_feed = pathlib.Path(__file__).parent / '..' / 'feed' / 'index.json'
    parser.set_defaults(show_profile_chooser=False,
                        config=default_config,
                        debug=False,
                        session_feed_url=default_feed.resolve().as_uri(),
                        update_cache=True,
                        delay_shutdown=False)
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    return args


def safe_check_dir(dirpath):
    try:
        if dirpath.is_dir():
            return True
        return False
    except PermissionError:
        logging.warning("%s PermissionError" % dirpath)
        return False


def check_media(args, config):
    if args.wait_for_media:
        while not safe_check_dir(config.video_cache_directory):
            logging.warning("%s does not exist. Waiting." % config.video_cache_directory)
            time.sleep(1)

        if config.warm_up_music_directory:
            while not safe_check_dir(config.warm_up_music_directory):
                logging.warning("%s does not exist. Waiting." % config.warm_up_music_directory)
                time.sleep(1)
    else:
        if not safe_check_dir(config.video_cache_directory):
            sys.exit("%s does not exist" % config.video_cache_directory)

        if config.warm_up_music_directory:
            if not safe_check_dir(config.warm_up_music_directory):
                logging.warning('Warm up music directory does not exist or is not a directory')
                config.warm_up_music_directory = None


class PiCaveApplication(Gtk.Application):
    class State:
        Initialising = 1
        ChoosingProfile = 2
        MainApplication = 3
        ShuttingDown = 4

    def __init__(self, args):
        super().__init__(flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.args = args
        self.window = None
        self.state = PiCaveApplication.State.Initialising
        self.connect('window-removed', self.on_window_removed)

    def do_startup(self):
        Gtk.Application.do_startup(self)

    def do_activate(self):
        if self.state == PiCaveApplication.State.Initialising:
            if not self.window:
                if self.args.show_profile_chooser:
                    self.state = PiCaveApplication.State.ChoosingProfile
                    self.window = ProfileChooserWindow(self.on_profile_chosen)
                    self.add_window(self.window)
                else:
                    self.on_profile_chosen(self.args.config)
            self.window.present()
        elif self.state in (PiCaveApplication.State.ChoosingProfile, PiCaveApplication.State.MainApplication):
            assert self.window
            self.window.present()

    def on_profile_chosen(self, config_path):
        if not config_path:
            print("No config file selected: exiting")
            self.state = PiCaveApplication.State.ShuttingDown
            self.quit()
            return

        logging.debug("Config file %s selected", config_path)

        if config_path.exists():
            self.config = config.Config(config_path)
        else:
            logging.warning("Configuration file not found")
            self.config = config.Config()

        if self.window:
            # it was the profile chooser: we've finished with it
            self.window.close()
            self.window.destroy()

        check_media(self.args, self.config)  # will sys.exit() if media do not exist

        self.state = PiCaveApplication.State.MainApplication

        video_feed = VideoFeed(self.args.session_feed_url)
        warm_up_mp3s = Mp3Index(self.config.warm_up_music_directory) if self.config.warm_up_music_directory else None
        video_cache = VideoCache(self.config, video_feed, self.args.update_cache)
        self.window = ApplicationWindow(self.config,
                                        warm_up_mp3s,
                                        video_feed,
                                        video_cache,
                                        self.args.hide_mouse_pointer,
                                        self.args.full_screen,
                                        self.args.delay_shutdown)
        self.add_window(self.window)
        self.window.present()

    def on_window_removed(self, application, window):
        logging.debug("on_window_removed - state %u; window %s" % (self.state, self.window))
        if (self.state == PiCaveApplication.State.MainApplication) and \
           (type(window) == ApplicationWindow) and \
           (window.show_profile_chooser):
            logging.debug("reinitialising")
            self.window = None
            self.state = PiCaveApplication.State.Initialising
            self.do_activate()
        logging.debug("-> %s" % self.window)


def main():
    args = parse_args()
    app = PiCaveApplication(args)
    app.run()


if __name__ == '__main__':
    main()
