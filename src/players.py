import json
import logging
import os
import socket
import subprocess


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
        if self.child:
            self.child.kill()
            self.child = None


class MPlayer(PlayerInterface):
    def __init__(self, exe, default_args):
        if default_args is None:
            default_args = ['-geometry', '0:0']
        super().__init__(exe, default_args)

    def play(self, filepath):
        cmd = [self.exe] + self.default_args + [filepath]
        self.child = subprocess.Popen(cmd,
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.DEVNULL,
                                      stderr=subprocess.DEVNULL)


class Mpg123(PlayerInterface):
    def __init__(self, exe, default_args):
        if default_args is None:
            default_args = ['--quiet', '--control']
        super().__init__(exe, default_args)

    def play(self, filepath):
        return self._play(filepath, allocate_pty=True)

    def play_pause(self):
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
        self.ipc_address = '/tmp/picave-mpv-socket'
        if default_args is None:
            default_args = ['--geometry=0:0', '--input-ipc-server=%s' % self.ipc_address]
        super().__init__(exe, default_args)

        self.pause = MPVPlayer.encode_command(['set_property_string', 'pause', 'yes'])
        self.resume = MPVPlayer.encode_command(['set_property_string', 'pause', 'no'])
        self.sock = None

        if os.path.exists(self.ipc_address):
            os.remove(self.ipc_address)

    def play(self, filepath):
        self.playing = True
        self.sock = None
        return self._play(filepath, allocate_pty=False)

    def play_pause(self):
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

    def play(self, filepath):
        cmd = [self.exe] + self.default_args + [filepath]
        self.child = subprocess.Popen(cmd,
                                      stdin=None,
                                      stdout=subprocess.DEVNULL,
                                      stderr=subprocess.DEVNULL)


class VlcPlayer(PlayerInterface):
    def __init__(self, exe, default_args):
        if default_args is None:
            default_args = []  # TODO: Better default arguments for VLC?
        super().__init__(exe, default_args)

    def play(self, filepath):
        cmd = [self.exe] + self.default_args + [filepath.resolve().as_uri()]
        subprocess.Popen(cmd)
