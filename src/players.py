from collections import namedtuple
import json
import logging
import os
import requests
import socket
import subprocess
import sys
import urllib.parse

try:
    # omxplayer is only available on Raspberry Pi
    from omxplayer.player import OMXPlayer  # noqa
    HAVE_OMXPLAYER = True
except ModuleNotFoundError:
    HAVE_OMXPLAYER = False

try:
    import vlc
    HAVE_LIBVLC = True
except ModuleNotFoundError:
    HAVE_LIBVLC = False

VideoSize = namedtuple('VideoSize', ['width', 'height'])

def clip(minval, val, maxval):
    return max(minval, min(val, maxval))

def get_video_size(filepath):
    result = subprocess.run(['ffprobe', '-v', 'error', '-print_format', 'json', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', str(filepath)],
                            capture_output=True, text=True)
    result = json.loads(result.stdout)
    return VideoSize(width=result['streams'][0]['width'], height=result['streams'][0]['height'])


class PlayerInterface(object):
    def __init__(self, exe, default_args, player_parameters):
        self.exe = exe
        self.default_args = default_args
        self.player_parameters = player_parameters
        self.child = None

    def is_finished(self):
        if self.child:
            finished = self.child.poll() is not None
            if finished:
                self.child = None
            return finished
        else:
            return True

    def _play(self, filepath, allocate_pty):
        cmd = [self.exe] + self.default_args + [filepath.resolve()]
        if allocate_pty:
            master, slave = os.openpty()
            self.child = subprocess.Popen(cmd,
                                          stdin=master,
                                          stdout=subprocess.DEVNULL,
                                          stderr=subprocess.DEVNULL)
            self.child_stdin = slave
        else:
            self.child = subprocess.Popen(cmd)
            self.child_stdin = None

    def play(self, filepath, widget=None):
        # default implementation
        return self._play(filepath, allocate_pty=False)

    def play_pause(self):
        raise NotImplementedError()

    def stop(self):
        logging.debug("PlayerInterface::stop (%s)", self.child)
        if self.child:
            self.child.kill()
            self.child = None

    def volume_change(self, change):
        pass

    def window_size_changed(self, new_size):
        pass


class MPlayer(PlayerInterface):
    def __init__(self, exe, default_args, player_parameters):
        self.fifo_name = '/tmp/picave.mplayer-fifo'
        if default_args is None:
            default_args = ['-geometry', '0:0',
                            '-slave',
                            '-input', 'file=%s' % self.fifo_name]
        super().__init__(exe, default_args, player_parameters)
        if os.path.exists(self.fifo_name):
            os.remove(self.fifo_name)

    def __del__(self):
        if os.path.exists(self.fifo_name):
            os.remove(self.fifo_name)

    def play(self, filepath, widget=None):
        # TODO: Switch to using _play() ?
        if not os.path.exists(self.fifo_name):
            os.mkfifo(self.fifo_name)
        cmd = [self.exe] + self.default_args + [filepath]
        self.child = subprocess.Popen(cmd,
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.DEVNULL)

    def play_pause(self):
        logging.debug("MPlayer::play_pause")
        self.send_command('pause')

    def send_command(self, command):
        with open(self.fifo_name, 'w') as handle:
            handle.write(command + '\n')

    def volume_change(self, change):
        logging.debug("MPlayer::volume_change %u", change)
        self.send_command('volume %u' % (10 if (change > 0) else -10))


class Mpg123(PlayerInterface):
    def __init__(self, exe, default_args, player_parameters):
        if default_args is None:
            default_args = ['--quiet', '--control']
        super().__init__(exe, default_args, player_parameters)

    def play(self, filepath, widget=None):
        return self._play(filepath, allocate_pty=True)

    def play_pause(self):
        logging.debug("Mpg123::play_pause")
        # Credit to https://stackoverflow.com/questions/17416158/python-2-7-subprocess-control-interaction-with-mpg123
        if self.child:
            logging.debug("Mpg123::play_pause")
            os.write(self.child_stdin, b's')

    def volume_change(self, change):
        if self.child:
            logging.debug("Mpg123::volume_change %u", change)
            change = b'+' if (change > 0) else b'-'
            change = 3 * change
            os.write(self.child_stdin, change)


class MPVPlayer(PlayerInterface):
    @staticmethod
    def encode_command(command):
        command = {'command': command}
        command = json.dumps(command) + '\n'
        command = command.encode()
        return command

    def __init__(self, exe, default_args, player_parameters):
        self.ipc_address = '/tmp/picave.mpv-socket'
        if default_args is None:
            default_args = ['--geometry=0:0', '--ontop', '--input-ipc-server=%s' % self.ipc_address]
        super().__init__(exe, default_args, player_parameters)

        self.pause = MPVPlayer.encode_command(['set_property_string', 'pause', 'yes'])
        self.resume = MPVPlayer.encode_command(['set_property_string', 'pause', 'no'])
        self.current_volume = 100
        self.sock = None

        if os.path.exists(self.ipc_address):
            os.remove(self.ipc_address)

    def __del__(self):
        if os.path.exists(self.ipc_address):
            os.remove(self.ipc_address)

    def play(self, filepath, widget=None):
        self.playing = True
        self.sock = None
        return self._play(filepath, allocate_pty=False)

    def play_pause(self):
        logging.debug("MPVPlayer::play_pause")
        self.send_command(self.pause if (self.playing) else self.resume)
        self.playing = not self.playing

    def send_command(self, command):
        if not self.child:
            return
        if self.sock is None:
            try:
                self.sock = socket.socket(socket.AF_UNIX)
                self.sock.connect(self.ipc_address)
            except FileNotFoundError:
                logging.debug("No socket found for MPV IPC")
                self.sock = None
                return

        logging.debug("MPVPlayer::send_command %s", command)
        self.sock.sendall(command)

    def volume_change(self, change):
        self.current_volume = clip(0, self.current_volume + 5 * change, 100)
        logging.debug("MPlayer::volume_change %u -> %u", change, self.current_volume)
        self.send_command(MPVPlayer.encode_command(['set_property', 'volume', self.current_volume]))


class OmxPlayer(PlayerInterface):
    def __init__(self, exe, default_args, player_parameters):
        if default_args is None:
            default_args = []
        super().__init__(exe, default_args, player_parameters)

    def playback_finished_handler(self, player, exit_status):
        self.child = None

    def play(self, filepath, widget=None):
        args = list(self.default_args)
        if widget:
            window = widget.get_allocation()
            video_size = get_video_size(filepath)
            logging.debug("OmxPlayer.play: window=%u,%u,%u,%u, video size=%s", window.x, window.y, window.width, window.height, str(video_size))
            width_ratio = window.width / video_size.width
            height_ratio = window.height / video_size.height
            draw_w = video_size.width * min(width_ratio, height_ratio)
            draw_h = video_size.height * min(width_ratio, height_ratio)
            assert draw_w <= window.width
            assert draw_h <= window.height
            draw_x1 = window.x + (window.width - draw_w)/2
            draw_y1 = window.y + (window.height - draw_h)/2
            draw_x2 = draw_x1 + draw_w
            draw_y2 = draw_y1 + draw_h
            args.extend(['--win', '%u,%u,%u,%u' % (draw_x1, draw_y1, draw_x2, draw_y2), '--aspect-mode', 'letterbox'])

        if HAVE_OMXPLAYER:
            # Use the wrapper, which allows full control
            self.child = OMXPlayer(filepath, args=args)
            self.child.exitEvent += self.playback_finished_handler
        else:
            logging.warning("Launching omxplayer without control")
            cmd = [self.exe] + args + [filepath]
            self.child = subprocess.Popen(cmd,
                                          stdin=None,
                                          stdout=subprocess.DEVNULL,
                                          stderr=subprocess.DEVNULL)

    def is_finished(self):
        if HAVE_OMXPLAYER:
            return self.child is None
        else:
            return super().is_finished()

    def play_pause(self):
        logging.debug("OmxPlayer::play_pause")
        if self.child and HAVE_OMXPLAYER:
            self.child.play_pause()

    def stop(self):
        logging.debug("OmxPlayer::stop")
        if HAVE_OMXPLAYER:
            if self.child:
                self.child.stop()
                self.child = None
            # else it's already terminated
        else:
            # Do not use super().stop(): omxplayer is a shell script that runs
            # omxplayer.bin
            # Killing omxplayer does not kill the actual video player, leaving
            # a full-screen application that cannot be terminated...
            subprocess.run(['pkill', 'omxplayer.bin'])

    def volume_change(self, change):
        if HAVE_OMXPLAYER and self.child:
            # omxplayer volume is [0, 10] - with 1 = 100%
            current_volume = self.child.volume()
            volume = clip(0, current_volume + change/10, 10)
            logging.debug("OmxPlayer::volume_change %u -> %u", current_volume, volume)
            self.child.set_volume(volume)


class LibVlcPlayer(PlayerInterface):
    def __init__(self, exe, default_args, player_parameters):
        assert HAVE_LIBVLC
        super().__init__(exe, default_args, player_parameters)
        self.video_player = None
        self.playing = False
        self.video_file_width = None  # The natural size of the video

    def is_finished(self):
        if self.video_player is None:
            return True
        logging.debug("is_finished: %f", self.video_player.get_position())
        return self.video_player.get_state() == vlc.State.Ended

    def play(self, filepath):
        self.playing = True
        self.video_file_width = get_video_size(filepath).width
        self.vlcInstance = vlc.Instance("--no-xlib")
        self.video_player = self.vlcInstance.media_player_new()
        self.video_player.set_mrl(filepath.as_uri())
        self.video_player.play()
        if widget:
            self.set_player_window(widget)
            self.set_video_scale(widget.get_allocation())

    def play_pause(self):
        # Must call play() before play_pause() will do anything
        assert self.video_player
        if self.playing:
            self.video_player.pause()
        else:
            self.video_player.play()
        self.playing = not self.playing

    def stop(self):
        if self.video_player:
            self.video_player.stop()
            self.video_player = None
            self.vlcInstance = None

    def window_size_changed(self, new_size):
        assert self.video_file_width
        self.set_video_scale(new_size)

    def set_video_scale(self, video_area_allocation):
        if video_area_allocation.width > self.video_file_width:
            # Don't attempt to scale up: the R-Pi isn't up to it
            self.video_player.video_set_scale(1.0)
        else:
            # automatically scale down to fit the window
            self.video_player.video_set_scale(0.0)

    def set_player_window(self, widget):
        logging.debug("set_player_window")
        if sys.platform == 'win32':
            raise NotImplementedError()
        elif sys.platform == 'darwin':
            self.set_player_window_darwin(widget)
        else:
            self.set_player_window_x11(widget)

    def set_player_window_darwin(self, widget):
        # https://gitlab.gnome.org/GNOME/pygobject/issues/112
        # and https://www.mail-archive.com/vlc-commits@videolan.org/msg55659.html
        # and https://github.com/oaubert/python-vlc/blob/master/examples/gtkvlc.py
        window = self.video_area.get_window()

        getpointer = ctypes.pythonapi.PyCapsule_GetPointer
        getpointer.restype = ctypes.c_void_p
        getpointer.argtypes = [ctypes.py_object]
        pointer = getpointer(window.__gpointer__, None)

        libgdk = ctypes.CDLL("libgdk-3.dylib")
        get_nsview = libgdk.gdk_quartz_window_get_nsview
        get_nsview.restype = ctypes.c_void_p
        get_nsview.argtypes = [ctypes.c_void_p]
        handle = get_nsview(pointer)

        self.video_player.set_nsobject(handle)

    def set_player_window_x11(self, widget):
        win_id = widget.get_window().get_xid()
        self.video_player.set_xwindow(win_id)

class VlcPlayer(PlayerInterface):
    def __init__(self, exe, default_args, player_parameters):
        self.vlc_port = 28771  # 28771 = 0x7063; 0x70=ord('p'), 0x63=ord('c')
        self.vlc_password = 'picave'
        if default_args is None:
            default_args = ['--video-on-top',
                            '--control', 'http',
                            '--http-host', 'localhost',
                            '--http-port', str(self.vlc_port),
                            '--http-password', self.vlc_password]
        super().__init__(exe, default_args, player_parameters)

    def play(self, filepath, widget=None):
        cmd = [self.exe] + self.default_args + [filepath.resolve().as_uri()]
        logging.debug("VlcPlayer::play %s", cmd)
        self.child = subprocess.Popen(cmd)

    def play_pause(self):
        logging.debug("VlcPlayer::play_pause")
        self.send_command(command='pl_pause')

    def send_command(self, **kwargs):
        if not self.child:
            return
        params = urllib.parse.urlencode(kwargs)
        addr = 'http://localhost:%u/requests/status.xml?%s' % (self.vlc_port, params)
        logging.debug("VlcPlayer::send_command %s", addr)
        response = requests.get(addr, auth=('', self.vlc_password))
        if not response.ok:
            logging.warning("VLC response: %s", response)

    def volume_change(self, change):
        change = '%+u' % (change * 8)
        self.send_command(command='volume', val=change)
