import logging

from config import Config
from stackwindowwithbutton import StackWindowWithButton


class PlayerWindowInterface(StackWindowWithButton):
    """
    A StackWindowWithButton whose content is a player of some kind
    """
    def __init__(self,
                 config: Config,
                 label: str):
        super().__init__(config, label)
        self.player = None  # set when we start playing

    def handle_volume_change(self, change):
        if self.player:
            self.player.volume_change(change)

    def is_playing(self):
        return self.player is not None

    def stop(self):
        logging.debug("PlayerWindowInterface: stop (%s)", self.player)
        if self.player:
            self.player.stop()
            self.player = None

    # inherited from StackWindow:
    #   add_windows_to_stack(self, stack, window_name_to_handler)
    #   play_pause(self)
