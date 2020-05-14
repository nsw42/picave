import json
import logging
import os
import requests
import socket
import subprocess

try:
    # omxplayer is only available on Raspberry Pi
    from omxplayer.player import OMXPlayer  # noqa
    HAVE_OMXPLAYER = True
except ModuleNotFoundError:
    HAVE_OMXPLAYER = False


class PlayerInterface(object):
    def __init__(self, exe, default_args):
        self.exe = exe
        self.default_args = default_args
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

    def play(self, filepath):
        # default implementation
        return self._play(filepath, allocate_pty=False)

    def play_pause(self):
        raise NotImplementedError()

    def stop(self):
        logging.debug("PlayerInterface::stop (%s)", self.child)
        if self.child:
            self.child.kill()
            self.child = None


class MPlayer(PlayerInterface):
    def __init__(self, exe, default_args):
        self.fifo_name = '/tmp/picave.mplayer-fifo'
        if default_args is None:
            default_args = ['-geometry', '0:0',
                            '-slave',
                            '-input', 'file=%s' % self.fifo_name]
        super().__init__(exe, default_args)
        if os.path.exists(self.fifo_name):
            os.remove(self.fifo_name)

    def __del__(self):
        if os.path.exists(self.fifo_name):
            os.remove(self.fifo_name)

    def play(self, filepath):
        # TODO: Switch to using _play() ?
        if not os.path.exists(self.fifo_name):
            os.mkfifo(self.fifo_name)
        cmd = [self.exe] + self.default_args + [filepath]
        self.child = subprocess.Popen(cmd,
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.DEVNULL)

    def play_pause(self):
        logging.debug("MPlayer::play_pause")
        with open(self.fifo_name, 'w') as handle:
            handle.write('pause\n')


class Mpg123(PlayerInterface):
    def __init__(self, exe, default_args):
        if default_args is None:
            default_args = ['--quiet', '--control']
        super().__init__(exe, default_args)

    def play(self, filepath):
        return self._play(filepath, allocate_pty=True)

    def play_pause(self):
        logging.debug("Mpg123::play_pause")
        # Credit to https://stackoverflow.com/questions/17416158/python-2-7-subprocess-control-interaction-with-mpg123
        if self.child:
            logging.debug("Mpg123::play_pause")
            os.write(self.child_stdin, b's')


class MPVPlayer(PlayerInterface):
    @staticmethod
    def encode_command(command):
        command = {'command': command}
        command = json.dumps(command) + '\n'
        command = command.encode()
        return command

    def __init__(self, exe, default_args):
        self.ipc_address = '/tmp/picave.mpv-socket'
        if default_args is None:
            default_args = ['--geometry=0:0', '--ontop', '--input-ipc-server=%s' % self.ipc_address]
        super().__init__(exe, default_args)

        self.pause = MPVPlayer.encode_command(['set_property_string', 'pause', 'yes'])
        self.resume = MPVPlayer.encode_command(['set_property_string', 'pause', 'no'])
        self.sock = None

        if os.path.exists(self.ipc_address):
            os.remove(self.ipc_address)

    def __del__(self):
        if os.path.exists(self.ipc_address):
            os.remove(self.ipc_address)

    def play(self, filepath):
        self.playing = True
        self.sock = None
        return self._play(filepath, allocate_pty=False)

    def play_pause(self):
        logging.debug("MPVPlayer::play_pause")
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

        command = self.pause if (self.playing) else self.resume
        logging.debug("MPVPlayer::play_pause %s", command)
        self.sock.sendall(command)
        self.playing = not self.playing


class OmxPlayer(PlayerInterface):
    def __init__(self, exe, default_args):
        if default_args is None:
            default_args = []
        super().__init__(exe, default_args)

    def playback_finished_handler(self, player, exit_status):
        self.child = None

    def play(self, filepath):
        if HAVE_OMXPLAYER:
            # Use the wrapper, which allows full control
            self.child = OMXPlayer(filepath, args=self.default_args)
            self.child.exitEvent += self.playback_finished_handler
        else:
            logging.warning("Launching omxplayer without control")
            cmd = [self.exe] + self.default_args + [filepath]
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


class VlcPlayer(PlayerInterface):
    def __init__(self, exe, default_args):
        self.vlc_port = 28771  # 28771 = 0x7063; 0x70=ord('p'), 0x63=ord('c')
        self.vlc_password = 'picave'
        if default_args is None:
            default_args = ['--video-on-top',
                            '--control', 'http',
                            '--http-host', 'localhost',
                            '--http-port', str(self.vlc_port),
                            '--http-password', self.vlc_password]
        super().__init__(exe, default_args)

    def play(self, filepath):
        cmd = [self.exe] + self.default_args + [filepath.resolve().as_uri()]
        self.child = subprocess.Popen(cmd)

    def play_pause(self):
        logging.debug("VlcPlayer::play_pause")
        if not self.child:
            return
        addr = 'http://localhost:%u/requests/status.xml?command=pl_pause' % self.vlc_port
        response = requests.get(addr, auth=('', self.vlc_password))
        if not response.ok:
            logging.warning("VLC response: %s", response)
