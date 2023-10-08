# pylint: disable=wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402

from editconfigdialog import EditConfigDialog  # noqa: E402
from stackwindowinterface import StackWindowInterface  # noqa: E402
# pylint: enable=wrong-import-position


class MainButtonWindow(StackWindowInterface):
    def __init__(self,
                 application_window,
                 button_providers):
        super().__init__()
        self.application_window = application_window
        self.button_providers = button_providers
        self.config = self.application_window.config

    def add_windows_to_stack(self, stack, window_name_to_handler):
        main_window_buttons = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_window_buttons.set_border_width(self.PADDING)

        config_button = Gtk.Button.new_from_icon_name('preferences-other-symbolic', Gtk.IconSize.BUTTON)
        config_button.set_halign(Gtk.Align.END)
        config_button.set_valign(Gtk.Align.START)
        config_button.connect('clicked', self.on_edit_config)
        main_window_buttons.pack_start(config_button, expand=False, fill=False, padding=0)

        focus_chain = []
        for provider in self.button_providers:
            main_window_buttons.pack_start(provider.button, expand=True, fill=True, padding=100)
            focus_chain.append(provider.button)
        window_name = "main_window_buttons"
        stack.add_named(main_window_buttons, window_name)
        window_name_to_handler[window_name] = self

        focus_chain.append(config_button)
        main_window_buttons.set_focus_chain(focus_chain)

    def on_edit_config(self, _):
        dialog = EditConfigDialog(parent=self.application_window, config=self.config)
        while True:
            response = dialog.run()
            if response != Gtk.ResponseType.OK:
                # User hit cancel. We're done.
                break

            error_msg = dialog.validate_input()
            if not error_msg:
                # User hit ok, and all the input was good
                dialog.write_values_to_config(self.config)
                self.config.save()
                break

            error_dialog = Gtk.MessageDialog(parent=None, modal=True, message_type=Gtk.MessageType.ERROR,
                                             buttons=Gtk.ButtonsType.OK,
                                             text=error_msg)
            error_dialog.set_position(Gtk.WindowPosition.CENTER)
            error_dialog.run()
            error_dialog.destroy()
            continue  # not needed, but helps code clarity, IMO
        dialog.destroy()

    def handle_volume_change(self, change):
        pass  # No effect on the main window

    def is_playing(self):
        return False

    def play_pause(self):
        pass  # No effect on the main window

    def stop(self):
        pass  # No effect on the main window
