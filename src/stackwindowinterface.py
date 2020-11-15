class StackWindowInterface(object):
    def __init__(self):
        self.PADDING = 200

    def add_windows_to_stack(self, stack, window_name_to_handler):
        raise NotImplementedError()

    def handle_volume_change(self, change):
        raise NotImplementedError()

    def is_playing(self):
        raise NotImplementedError()

    def play_pause(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()
