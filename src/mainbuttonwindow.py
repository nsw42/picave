from stackwindowinterface import StackWindowInterface

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402 # need to call require_version before we can call this


class MainButtonWindow(StackWindowInterface):
    def __init__(self,
                 button_providers):
        super().__init__()
        self.button_providers = button_providers

    def add_windows_to_stack(self, stack, window_name_to_handler):
        main_window_buttons = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_window_buttons.set_border_width(self.PADDING)
        for provider in self.button_providers:
            main_window_buttons.pack_start(provider.button, expand=True, fill=True, padding=100)
        window_name = "main_window_buttons"
        stack.add_named(main_window_buttons, window_name)
        window_name_to_handler[window_name] = self

    def handle_volume_change(self, change):
        pass  # No effect on the main window

    def is_playing(self):
        return False

    def play_pause(self):
        pass  # No effect on the main window

    def stop(self):
        pass  # No effect on the main window
