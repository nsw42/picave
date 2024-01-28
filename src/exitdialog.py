from enum import Enum

# pylint: disable=wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402
# pylint: enable=wrong-import-position


ExitChoices = Enum('ExitChoices', ['Cancel', 'ChangeProfile', 'Quit', 'Shutdown'])


class ExitDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(title="Really quit?",
                         parent=parent,
                         flags=0)
        self.do_auto_update_checkbox = Gtk.CheckButton.new_with_label("Check for updates")
        self.do_auto_update_checkbox.set_active(False)
        content_box = self.get_content_area()
        content_box.pack_end(self.do_auto_update_checkbox, expand=True, fill=False, padding=4)

        self.add_button(Gtk.STOCK_CANCEL, ExitChoices.Cancel.value)
        self.add_button("Change profile", ExitChoices.ChangeProfile.value)
        self.add_button("Quit", ExitChoices.Quit.value)
        self.add_button("Shutdown", ExitChoices.Shutdown.value)
        self.set_default_size(150, 100)

        self.show_all()

    def do_auto_update(self):
        return self.do_auto_update_checkbox.get_active()
