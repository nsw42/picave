from argparse import ArgumentParser
import logging
import pathlib
import sys
import time

# pylint: disable=wrong-import-position
import gi
gi.require_versions({
    'Gtk': '3.0',
})
from gi.repository import Gio, Gtk  # noqa: E402

from applicationwindow import ApplicationWindow  # noqa: E402
from config import Config, default_config_path, LoadException  # noqa: E402
from mp3index import Mp3Index  # noqa: E402
from profilechooserwindow import ProfileChooserWindow  # noqa: E402
from videocache import VideoCache  # noqa: E402
from videofeed import VideoFeed  # noqa: E402
# pylint: enable=wrong-import-position


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
    default_config = default_config_path()
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
        logging.warning(f"{dirpath} PermissionError")
        return False


def check_media(args, config):
    if args.wait_for_media:
        while not safe_check_dir(config.video_cache_directory):
            logging.warning(f"{config.video_cache_directory} does not exist. Waiting.")
            time.sleep(1)

        if config.warm_up_music_directory:
            while not safe_check_dir(config.warm_up_music_directory):
                logging.warning(f"{config.warm_up_music_directory} does not exist. Waiting.")
                time.sleep(1)
    else:
        if not safe_check_dir(config.video_cache_directory):
            sys.exit(f"{config.video_cache_directory} does not exist")

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
        self.config = None
        self.window = None
        self.state = PiCaveApplication.State.Initialising
        self.connect('window-removed', self.on_window_removed)

    def do_startup(self, *args, **kwargs):
        Gtk.Application.do_startup(self, *args, **kwargs)

    def do_activate(self, *args, **kwargs):
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
            try:
                self.config = Config(config_path)
            except LoadException as e:
                logging.warning(f"Validation failure when loading file {config_path}")
                alert = Gtk.MessageDialog(parent=None,
                                          modal=True,
                                          message_type=Gtk.MessageType.WARNING,
                                          buttons=Gtk.ButtonsType.OK,
                                          text=f"Validation failure when loading the file:\n{str(e)}")
                alert.set_position(Gtk.WindowPosition.CENTER)
                alert.run()
                alert.destroy()
                # We want to leave the profile chooser window open, but the profile chooser
                # has a 'run once' semantic.
                if self.window:
                    self.window.close()
                    self.window.destroy()
                    self.window = None
                if self.args.show_profile_chooser:
                    self.state = PiCaveApplication.State.Initialising
                    self.do_activate()
                    return
                self.config = Config()
        else:
            logging.warning("Configuration file not found")
            alert = Gtk.MessageDialog(parent=None,
                                      modal=True,
                                      message_type=Gtk.MessageType.WARNING,
                                      buttons=Gtk.ButtonsType.OK,
                                      text=f"Configuration file {config_path} not found")
            alert.set_position(Gtk.WindowPosition.CENTER)
            alert.run()
            alert.destroy()
            self.config = Config()

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

    def on_window_removed(self, _application, window):
        logging.debug(f"on_window_removed - state {self.state}; window {self.window}")
        if (self.state == PiCaveApplication.State.MainApplication) and \
           (isinstance(window, ApplicationWindow)) and \
           (window.show_profile_chooser):
            logging.debug("reinitialising")
            self.window = None
            self.state = PiCaveApplication.State.Initialising
            self.do_activate()
        logging.debug(f"-> {self.window}")


def main():
    args = parse_args()
    app = PiCaveApplication(args)
    app.run()


if __name__ == '__main__':
    main()
