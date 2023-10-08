from abc import abstractmethod

# pylint: disable=wrong-import-position
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402

from config import Config  # noqa: E402
from stackwindowinterface import StackWindowInterface  # noqa: E402
# pylint: enable=wrong-import-position


class StackWindowWithButtonInterface(StackWindowInterface):
    """
    Extends StackWindowInterface for windows that do the following:
        * create a button, which is to be shown on the front page
        * create one or more windows, to show some content
        * set up the click handler for that button to switch the stack to the appropriate window
    """
    def __init__(self,
                 config: Config,
                 label: str):
        super().__init__()
        self.stack = None  # initialised during add_windows_to_stack
        self.config = config
        self.button = Gtk.Button(label=label)
        self.button.connect("clicked", self.on_main_button_clicked)

    @abstractmethod
    def on_main_button_clicked(self, widget):
        raise NotImplementedError()  # to be overridden by the relevant stack window class

    # inherited from StackWindowInterface:
    #   add_windows_to_stack(self, stack, window_name_to_handler)
    #   handle_volume_change
    #   is_playing
    #   play_pause(self)
    #   stop
