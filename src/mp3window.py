import datetime
import logging

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


class Mp3Window(PlayerWindowInterface):
    def __init__(self,
                 config: Config,
                 label: str,
                 mp3index: Mp3Index):
        super().__init__(config, label)
        self.mp3index = mp3index
        self.button.set_sensitive(self.mp3index is not None)
        self.paused_elapsed = None

    def add_windows_to_stack(self, stack, window_name_to_handler):
        self.stack = stack

        self.artist_label = Gtk.Label()
        self.artist_label.set_label("<artist>")
        self.artist_label.set_hexpand(True)
        self.artist_label.set_vexpand(True)

        self.title_label = Gtk.Label()
        self.title_label.set_label("<title>")
        self.title_label.set_hexpand(True)
        self.title_label.set_vexpand(True)

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

        time_hbox = Gtk.HBox()
        time_hbox.pack_start(self.time_label, expand=True, fill=True, padding=0)
        time_hbox.pack_start(self.duration_label, expand=True, fill=True, padding=0)
        time_hbox.set_hexpand(True)
        time_hbox.set_vexpand(True)

        self.pad = Gtk.Fixed()

        self.next_button = Gtk.Button(label="Next track")
        self.next_button.connect('clicked', self.on_next_button_clicked)

        self.back_button = Gtk.Button(label="Back")
        self.back_button.connect('clicked', self.on_back_button_clicked)

        #       0         1             2
        #  0            artist
        #  1   pad      label         Next
        #  2        time/duration
        #  3            Back

        grid = Gtk.Grid()
        grid.attach(self.pad, left=0, top=1, width=1, height=1)
        grid.attach(self.artist_label, left=1, top=0, width=1, height=1)
        grid.attach(self.title_label, left=1, top=1, width=1, height=1)
        grid.attach(time_hbox, left=1, top=2, width=1, height=1)

        self.next_button.set_vexpand(False)
        grid.attach(self.next_button, left=2, top=1, width=1, height=1)

        self.back_button.set_hexpand(True)
        self.back_button.set_size_request(0, 80)  # only sets height of button - width is set by grid
        grid.attach(self.back_button, left=0, top=3, width=3, height=1)

        grid.set_border_width(200)
        window_name = "mp3_info_box"
        stack.add_named(grid, window_name)
        window_name_to_handler[window_name] = self

        grid.connect('realize', self.on_shown)

    def on_back_button_clicked(self, widget):
        self.stop()
        self.stack.set_visible_child_name("main_window_buttons")

    def on_main_button_clicked(self, widget):
        self.play_random_file()
        assert self.stack
        self.stack.set_visible_child_name("mp3_info_box")
        GLib.timeout_add_seconds(1, self.on_timer_tick)

    def on_next_button_clicked(self, widget):
        self.stop()
        self.play_random_file()

    def on_size_allocate(self, widget, allocation):
        self.pad.set_size_request(self.next_button.get_preferred_width().natural_width, 32)

    def on_shown(self, widget):
        self.next_button.grab_focus()

    def on_timer_tick(self):
        if self.player:
            if self.paused_elapsed:
                delta = self.paused_elapsed
            elif self.play_started_at:
                delta = datetime.datetime.now() - self.play_started_at
            else:
                delta = datetime.timedelta(seconds=0)  # Should never happen
            time_str = format_mm_ss(delta.seconds) + ' '
            self.time_label.set_label(time_str)

            if self.player.is_finished():
                self.play_random_file()
            return True
        else:
            return False  # don't call me again

    def trim_text_to_pixels(self, label, text_lines, max_width=None):
        if max_width is None:
            max_width = self.stack.get_allocation().width - 2 * self.PADDING
            max_width -= 2 * self.next_button.get_preferred_width().natural_width
        logging.debug("Max width is %u" % max_width)
        layout = label.create_pango_layout()
        for line_number in range(len(text_lines)):
            text = text_lines[line_number]
            while text != ' ...':
                layout.set_text(text, len(text))
                ink, logical = layout.get_pixel_extents()
                logging.debug("%s is %u pixels wide" % (text, logical.width))
                if logical.width < max_width:
                    break  # this text is short enough
                text = text[:-5] + ' ...'  # makes the text one character shorter
            text_lines[line_number] = text
        return text_lines

    def play_random_file(self):
        mp3filename = self.mp3index.random_file()
        reader = mutagen.File(mp3filename)
        artist = reader.tags.get('TPE1')
        if artist:
            artist_text = self.trim_text_to_pixels(self.artist_label, artist.text)
            self.artist_label.set_label('\n'.join(artist_text))
        title = reader.tags.get('TIT2')
        if title:
            title_text = self.trim_text_to_pixels(self.title_label, title.text)
            self.title_label.set_label('\n'.join(title_text))
        duration_ss = reader.info.length
        if duration_ss:
            self.time_label.set_label(format_mm_ss(0) + ' ')
            self.duration_label.set_label('/ %s' % format_mm_ss(duration_ss))
            self.play_started_at = datetime.datetime.now()
        else:
            self.time_label.set_label('')
            self.duration_label.set_label('')
            self.play_random_file = None  # don't attempt to show time in file
        self.player = self.config.players['.mp3']
        self.player.play(mp3filename)
        self.on_size_allocate(None, None)  # do this here rather than wait for 'allocated' signal to avoid screen jiggle
        self.paused_elapsed = None

    def play_pause(self):
        if self.player:
            self.player.play_pause()
            if self.paused_elapsed:
                # We were paused; now restarting
                self.play_started_at = datetime.datetime.now() - self.paused_elapsed
                self.paused_elapsed = None
            else:
                self.paused_elapsed = datetime.datetime.now() - self.play_started_at
            self.on_timer_tick()
