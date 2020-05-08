import ctypes
import os.path
import select
import sys

# python-libinput exists and would do all of this for us,
# but pip install on the Pi only finds v0.1.0, and that
# version makes it hard/impossible to poll for input events.
# (get_events() can take a timeout parameter, but it only
# works if timeout > 0)
# Since our needs are simple, we roll our own.

# Relevant event type constants
EV_KEY = 1

# Relevant key identifier constants
KEY_BACK = 158
KEY_STOP = 128
KEY_PLAYPAUSE = 164

# TODO: This is correct for the Raspberry Pi,
# but not for all platforms
class Timeval(ctypes.Structure):
    _fields_ = [("sec", ctypes.c_int),
                ("usec", ctypes.c_int)]


class Event(ctypes.Structure):
    _fields_ = [("timeval", Timeval),
                ("type",    ctypes.c_ushort),
                ("code",    ctypes.c_ushort),
                ("value",   ctypes.c_int)]

class KeyboardEvent(object):
    def __init__(self, event_struct):
        self.time = event_struct.timeval.sec + event_struct.timeval.usec / 1000000
        self.key = event_struct.code
        self.pressed = event_struct.value


class OsmcRemoteControl(object):
    def __init__(self, input_filepath):
        self.handle = open(input_filepath, 'rb')

    def poll_for_key_event(self):
        readable, writable, excepted = select.select([self.handle],
                                                     [],
                                                     [],
                                                     0.0)
        if not readable:
            return None

        event = self.handle.read(ctypes.sizeof(Event))
        event = Event.from_buffer_copy(event)
        if event.type != EV_KEY:
            return None

        return KeyboardEvent(event)


class DebouncedOsmcRemoteControl(OsmcRemoteControl):
    def __init__(self, input_filepath, debounce_interval=1.0):
        super().__init__(input_filepath)
        self.last_keydown_event = None
        self.debounce_interval = debounce_interval

    def poll_for_key_event(self):
        event = super().poll_for_key_event()

        # only act on key-down events; discard releases
        if (event is None) or (not event.pressed):
            return None

        # debounce
        prev_keydown_event = self.last_keydown_event
        self.last_keydown_event = event
        if (prev_keydown_event) \
                and (prev_keydown_event.key == event.key) \
                and (event.time - prev_keydown_event.time < self.debounce_interval):
            # print("<Ignoring key - debounce>")
            return None

        return event


def look_for_osmc():
    """
    Look for an appropriate /dev/input source and return a
    DebouncedOsmcRemoteControl if it is found.
    Returns None if no such event source can be found.
    """
    filename = '/dev/input/by-id/usb-OSMC_Remote_Controller_USB_Keyboard_Mouse-event-if01'
    if os.path.exists(filename):
        return DebouncedOsmcRemoteControl(filename)

    return None
