from argparse import ArgumentParser
import pathlib

import vlc

from videofeed import VideoFeed

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402 # need to call require_version before we can call this

# gi.require_version('GdkX11', '3.0')
# from gi.repository import GdkX11


class ApplicationWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Pi Cave")
        self.connect("destroy", Gtk.main_quit)
        self.connect("delete-event", Gtk.main_quit)

    def setup_objects_and_events(self):
        self.set_border_width(200)

        self.main_session_button = Gtk.Button(label="Main session")
        self.main_session_button.connect("clicked", self.on_main_session_clicked)

        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.vbox)
        self.vbox.pack_start(self.main_session_button, expand=True, fill=True, padding=250)

        self.set_size_request(1920, 1000)

    def on_main_session_clicked(self, widget):
        pass


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('--session-feed-url', metavar='URL', action='store',
                        help="Specify where to find the session video index feed. "
                             "Default %(default)s")
    default_feed = pathlib.Path(__file__).parent / '..' / 'feed' / 'index.json'
    parser.set_defaults(session_feed_url=default_feed.resolve().as_uri())
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    video_feed = VideoFeed.init_from_feed_url(args.session_feed_url)

    window = ApplicationWindow()
    window.setup_objects_and_events()
    window.show_all()
    Gtk.main()


if __name__ == '__main__':
    main()
