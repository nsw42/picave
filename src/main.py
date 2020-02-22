import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
# gi.require_version('GdkX11', '3.0')
# from gi.repository import GdkX11

import vlc


class ApplicationWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Pi Cave")
        self.player_paused=False
        self.is_player_active = False
        self.connect("destroy", Gtk.main_quit)
        self.connect("delete-event", Gtk.main_quit)

    def show(self):
        self.show_all()
    
    def setup_objects_and_events(self):
        self.playback_button = Gtk.Button()
        self.stop_button = Gtk.Button()

        self.play_image = Gtk.Image.new_from_icon_name(
                "gtk-media-play",
                Gtk.IconSize.MENU
            )
        self.pause_image = Gtk.Image.new_from_icon_name(
                "gtk-media-pause",
                Gtk.IconSize.MENU
            )
        self.stop_image = Gtk.Image.new_from_icon_name(
                "gtk-media-stop",
                Gtk.IconSize.MENU
            )

        self.playback_button.set_image(self.play_image)
        self.stop_button.set_image(self.stop_image)

        # self.playback_button.connect("clicked", self.toggle_player_playback)
        # self.stop_button.connect("clicked", self.stop_player)

        self.draw_area = Gtk.DrawingArea()
        self.draw_area.set_size_request(300,300)

        # self.draw_area.connect("realize", self._realized)

        self.hbox = Gtk.Box(spacing=6)
        self.hbox.pack_start(self.playback_button, True, True, 0)
        self.hbox.pack_start(self.stop_button, True, True, 0)

        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.vbox)
        self.vbox.pack_start(self.draw_area, True, True, 0)
        self.vbox.pack_start(self.hbox, False, False, 0)


def main():
    window = ApplicationWindow()
    window.setup_objects_and_events()
    window.show()
    Gtk.main()


if __name__ == '__main__':
    main()
