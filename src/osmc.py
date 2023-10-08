import ctypes
import os
import subprocess
import sys
import time

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


# This is correct for the Raspberry Pi,
# but possibly not for all platforms
# Call selftest() to check.
# If something is wrong, see your definition of struct timeval
# start looking in /usr/include/time.h
class Timeval(ctypes.Structure):
    _fields_ = [("sec", ctypes.c_int),
                ("usec", ctypes.c_int)]


class Event(ctypes.Structure):
    _fields_ = [("timeval", Timeval),
                ("type", ctypes.c_ushort),
                ("code", ctypes.c_ushort),
                ("value", ctypes.c_int)]


class KeyboardEvent(object):
    def __init__(self, event_struct):
        self.time = event_struct.timeval.sec + event_struct.timeval.usec / 1000000
        self.key = event_struct.code
        self.pressed = event_struct.value

    def __str__(self):
        return f'({"pressed" if self.pressed else "released"} K:{self.key})'


class OsmcRemoteControl(object):
    def __init__(self, input_filepath):
        self.handle = os.open(input_filepath, os.O_RDONLY | os.O_EXCL | os.O_NDELAY)
        self.accum = b''

    def poll_for_key_event(self):
        to_read = ctypes.sizeof(Event) - len(self.accum)

        try:
            self.accum += os.read(self.handle, to_read)
        except BlockingIOError:
            return None
        if len(self.accum) < ctypes.sizeof(Event):
            return None

        assert len(self.accum) == ctypes.sizeof(Event)
        event = Event.from_buffer_copy(self.accum)

        self.accum = b''

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


def look_for_osmc(debounce=True):
    """
    Look for an appropriate /dev/input source and return a
    [Debounced]OsmcRemoteControl if it is found.
    Returns None if no such event source can be found.
    """
    filename = '/dev/input/by-id/usb-OSMC_Remote_Controller_USB_Keyboard_Mouse-event-if01'
    if os.path.exists(filename):
        factory = DebouncedOsmcRemoteControl if debounce else OsmcRemoteControl
        return factory(filename)

    return None


def poll(debounce):
    osmc = look_for_osmc(debounce)
    if not osmc:
        sys.exit("No OSMC input found")
    print(f"Polling for events with {osmc}:")
    start = time.time()
    while time.time() < start + 60:
        event = osmc.poll_for_key_event()
        if event:
            print(event)
        time.sleep(0.1)


def selftest():
    failed = False
    if not selftest_one('struct timeval tv;', 'sizeof(tv.tv_sec)', ctypes.sizeof(ctypes.c_int)):
        failed = True
    if not selftest_one('struct timeval tv;', 'sizeof(tv.tv_usec)', ctypes.sizeof(ctypes.c_int)):
        failed = True
    if not selftest_one('struct timeval tv;', 'sizeof(tv)', ctypes.sizeof(Timeval)):
        failed = True
    if not selftest_one('struct input_event ev;', 'sizeof(ev)', ctypes.sizeof(Event)):
        failed = True
    if not selftest_one('struct input_event ev;', 'sizeof(ev.time)', ctypes.sizeof(Timeval)):
        failed = True
    if not selftest_one('struct input_event ev;', 'sizeof(ev.type)', ctypes.sizeof(ctypes.c_ushort)):
        failed = True
    if not selftest_one('struct input_event ev;', 'sizeof(ev.code)', ctypes.sizeof(ctypes.c_ushort)):
        failed = True
    if not selftest_one('struct input_event ev;', 'sizeof(ev.value)', ctypes.sizeof(ctypes.c_int)):
        failed = True

    if failed:
        sys.exit("self-test failed")
    else:
        print("self-test passed")


def selftest_one(vardecl, sizeof_expr, expected_size):
    with open('/tmp/osmc_sizeof.c', 'w', encoding='utf-8') as handle:
        print('''
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <linux/input.h>
int main(void) {
''', file=handle)
        print(f'{vardecl}', file=handle)
        print(r'printf("%u\n", ' + sizeof_expr + ');', file=handle)
        print('return 0;', file=handle)
        print('}', file=handle)
    subprocess.run(['gcc', '-o', '/tmp/osmc_sizeof', '/tmp/osmc_sizeof.c'], check=True)
    output = subprocess.run(['/tmp/osmc_sizeof'], capture_output=True, check=True, text=True)
    actual_size = int(output.stdout.strip())
    if actual_size != expected_size:
        print(f"{vardecl} {sizeof_expr} gave {actual_size}; expected {expected_size}")
        return False
    return True


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else None
    if command == 'selftest':
        selftest()
    elif command == 'poll':
        if len(sys.argv) <= 2:
            debounce = True
        else:
            debounce = (sys.argv[2] == 'no-debounce')
        poll(debounce)
    else:
        print(f"Usage: {sys.argv[0]} COMMAND")
        print("Command is one of:")
        print("  selftest - to check the size of structures")
        print("  poll - to poll for events and print them as they happen")


if __name__ == '__main__':
    main()
