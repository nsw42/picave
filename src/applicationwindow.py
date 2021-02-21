from enum import Enum
import logging
import subprocess
import sys

import config
from mainbuttonwindow import MainButtonWindow
from mp3index import Mp3Index
from mp3window import Mp3Window
import osmc
from sessionwindow import SessionWindow
from videocache import VideoCache
from videofeed import VideoFeed
from videoindexwindow import VideoIndexWindow

import gi
gi.require_versions({
    'GLib': '2.0',
    'Gdk': '3.0',
    'Gtk': '3.0',
})
from gi.repository import Gdk, GLib, Gtk  # noqa: E402 # need to call require_version before we can call this


ExitChoices = Enum('ExitChoices', ['Cancel', 'ChangeProfile', 'Quit', 'Shutdown'])


class ExitDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(title="Really quit?",
                         parent=parent,
                         flags=0)
        self.add_button(Gtk.STOCK_CANCEL, ExitChoices.Cancel.value)
        self.add_button("Change profile", ExitChoices.ChangeProfile.value)
        self.add_button("Quit", ExitChoices.Quit.value)
        self.add_button("Shutdown", ExitChoices.Shutdown.value)
        self.set_default_size(150, 100)

        self.show_all()


class ApplicationWindow(Gtk.Window):
    """
    Main application window.
    Creates and manages the following window hierarchy:
     * main window
       * Stack
         * main window buttons
           * Button("Main session") (clicking shows the main session video index)
         * main session index (a listbox of videos)
    """
    stack_window_parents = {
        "main_window_buttons": None,
        "mp3_info_box": "main_window_buttons",
        "main_session_index_window": "main_window_buttons",
        "interval_window": "main_session_index_window"
    }

    def __init__(self,
                 config: config.Config,
                 mp3index: Mp3Index,
                 main_session_feed: VideoFeed,
                 video_cache: VideoCache,
                 hide_mouse_pointer: bool,
                 full_screen: bool):
        self.config = config
        self.main_session_feed = main_session_feed
        self.video_cache = video_cache
        self.hide_mouse_pointer = hide_mouse_pointer
        self.show_profile_chooser = None  # set to True/False depending on how the window is closed
        Gtk.Window.__init__(self, title="Pi Cave")
        self.connect("realize", self.on_realized)
        self.connect("destroy", self.on_window_closed)
        self.connect("delete-event", self.on_window_closed)

        self.key_table = []
        for (keyname, handler) in [
            ('<Primary>Q', self.on_quit),
            ('Escape', self.on_show_home),  # OSMC 'Home' button
            ('<Shift>Escape', self.do_quit_dialog),
            ('c', self.on_show_index),  # OSMC 'index' button
            ('P', self.on_play_pause),  # TODO: Remove me
            ('X', self.on_back_button),  # TODO: Remove me
            ('Z', self.on_stop_button),  # TODO: Remove me
            ('<Shift>plus', self.on_volume_up),  # TODO: Remove me
            ('equal', self.on_volume_up),  # OSMC 'Vol +'
            ('minus', self.on_volume_down),  # OSMC 'Vol -'
        ]:
            keyval, mods = Gtk.accelerator_parse(keyname)
            if keyval:
                logging.debug("%s + %s -> %s", mods, keyval, handler)
                self.key_table.append((keyval, mods, handler))
            else:
                logging.warning("Unable to parse accelerator %s", keyname)
        self.connect('key-press-event', self.on_key_press)

        self.warmup_handler = Mp3Window(self.config, "Warm up", mp3index)
        self.main_session_handler = SessionWindow(self.config, "", main_session_feed.url)
        self.video_index_window = VideoIndexWindow(self.config,
                                                   "Main session",
                                                   main_session_feed,
                                                   self.video_cache,
                                                   self.main_session_handler)
        self.main_buttons = MainButtonWindow([self.warmup_handler,
                                              self.video_index_window])

        if full_screen:
            self.fullscreen()
        else:
            display = Gdk.Display().get_default()
            monitor = display.get_primary_monitor()
            workarea = monitor.get_workarea()
            self.set_size_request(workarea.width, workarea.height)

        self.stack = Gtk.Stack()
        self.add(self.stack)
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(1000)

        self.window_name_to_handler = {}

        self.main_buttons.add_windows_to_stack(self.stack, self.window_name_to_handler)
        self.warmup_handler.add_windows_to_stack(self.stack, self.window_name_to_handler)
        self.video_index_window.add_windows_to_stack(self.stack, self.window_name_to_handler)
        self.main_session_handler.add_windows_to_stack(self.stack, self.window_name_to_handler)

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
                osmc.KEY_STOP: self.on_stop_button,
            }
            GLib.timeout_add(50, self.check_osmc_events)  # 50ms = 1/20s

        self.show_all()

    def check_osmc_events(self):
        event = self.osmc.poll_for_key_event()
        if event:
            logging.debug("OSMC %u", event.key)
            handler = self.osmc_handlers.get(event.key)
            if handler:
                handler()
        return True  # keep looking for OSMC events

    def do_quit_dialog(self):
        dialog = ExitDialog(self)
        response = dialog.run()
        dialog.destroy()

        logging.debug("Response %u", response)

        if response == ExitChoices.Cancel.value:
            # No action required
            pass
        elif response == ExitChoices.ChangeProfile.value:
            self.on_change_profile()
        elif response == ExitChoices.Quit.value:
            self.on_quit()
        elif response == ExitChoices.Shutdown.value:
            self.on_shutdown()

    def do_stop_or_back(self, show_quit_dialog):
        current_window = self.stack.get_visible_child_name()
        logging.debug("do_stop_or_back: current_window=%s", current_window)
        if current_window in self.stack_window_parents:
            parent = self.stack_window_parents[current_window]
            logging.debug(".. parent=%s", parent)
            if parent:
                stack_window = self.window_name_to_handler[current_window]
                stack_window.stop()
                self.stack.set_visible_child_name(parent)
            else:
                if show_quit_dialog:
                    self.do_quit_dialog()

        else:
            logging.debug("Internal error: No parent window found for %s", current_window)
            self.on_show_home()

    def on_key_press(self, widget, event):
        logging.debug('Key: hw: %s / state: %s / keyval: %s' % (event.hardware_keycode, event.state, event.keyval))
        event_mods = event.state
        if sys.platform == 'darwin':
            # Command-Q is shown as GDK_MOD2_MASK | GDK_META_MASK
            # yet accelerator_parse('<Primary>Q') returns
            # just GDK_META_MASK. As we don't currently use
            # GDK_MOD2_MASK for anything else, this is a quick
            # hack.
            # But (flags &~ Gdk.ModifierType.MOD2_MASK) returns
            # an int, rather than a Gdk.ModifierType - hence
            # this convoluted expression.
            event_mods = (event_mods | Gdk.ModifierType.MOD2_MASK) ^ Gdk.ModifierType.MOD2_MASK
        for (keyval, mods, handler) in self.key_table:
            if (event_mods == mods) and (event.keyval == keyval):
                handler()
                return True  # we've handled the event
        return False

    def on_back_button(self):
        self.do_stop_or_back(show_quit_dialog=True)

    def get_visible_stack_window(self):
        current_window = self.stack.get_visible_child_name()
        logging.debug("get_visible_stack_window: current window %s", current_window)
        stack_window = self.window_name_to_handler[current_window]
        logging.debug("  %s", stack_window)
        return stack_window

    def on_play_pause(self):
        stack_window = self.get_visible_stack_window()
        stack_window.play_pause()

    def on_show_home(self):
        self.stop_playing()
        self.stack.set_visible_child_name("main_window_buttons")

    def on_show_index(self):
        self.stop_playing()
        self.video_index_window.on_main_button_clicked(None)

    def on_change_profile(self, *args):
        self.show_profile_chooser = True
        self.stop_playing()
        self.video_cache.stop_download()
        self.destroy()

    def on_quit(self, *args):
        self.show_profile_chooser = False
        self.stop_playing()
        self.video_cache.stop_download()
        self.get_application().quit()

    def on_realized(self, *args):
        if self.hide_mouse_pointer:
            self.get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.BLANK_CURSOR))

    def on_shutdown(self, *args):
        self.on_quit()
        subprocess.run(['sudo', 'shutdown', '-h', '+1'])  # give a minute to interrupt (shutdown -c)

    def on_stop_button(self):
        stack_window = self.get_visible_stack_window()
        if stack_window.is_playing():
            self.do_stop_or_back(show_quit_dialog=False)

    def on_volume_change(self, change):
        logging.debug("on_volume_change: %u", change)
        stack_window = self.get_visible_stack_window()
        stack_window.handle_volume_change(change)

    def on_volume_down(self):
        self.on_volume_change(-1)

    def on_volume_up(self):
        self.on_volume_change(1)

    def stop_playing(self):
        self.warmup_handler.stop()
        self.main_session_handler.stop()

    def on_window_closed(self):
        if self.show_profile_chooser is None:
            self.show_profile_chooser = False
