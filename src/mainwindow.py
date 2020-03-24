from stackwindow import StackWindow

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402 # need to call require_version before we can call this


class MainButtonWindow(StackWindow):
    def __init__(self,
                 button_providers):
        super().__init__()
        self.button_providers = button_providers

    def add_windows_to_stack(self, stack):
        main_window_buttons = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_window_buttons.set_border_width(200)
        for provider in self.button_providers:
            main_window_buttons.pack_start(provider.button, expand=True, fill=True, padding=100)
        stack.add_named(main_window_buttons, "main_window_buttons")
