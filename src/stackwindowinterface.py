from abc import ABC, abstractmethod


class StackWindowInterface(ABC):
    def __init__(self):
        self.PADDING = 200

    @abstractmethod
    def add_windows_to_stack(self, stack, window_name_to_handler):
        raise NotImplementedError()

    @abstractmethod
    def handle_volume_change(self, change):
        raise NotImplementedError()

    @abstractmethod
    def is_playing(self):
        raise NotImplementedError()

    @abstractmethod
    def play_pause(self):
        raise NotImplementedError()

    @abstractmethod
    def stop(self):
        raise NotImplementedError()
