import datetime

import mutagen

from config import Config
from mp3index import Mp3Index
from utils import format_mm_ss
from windowinterface import PlayerWindowInterface

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402 # need to call require_version before we can call this
gi.require_version('GLib', '2.0')
from gi.repository import GLib  # noqa: E402 # need to call require_version before we can call this
gi.require_version('Pango', '1.0')
from gi.repository import Pango  # noqa: E402 # need to call require_version before we can call this


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
