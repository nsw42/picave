import subprocess


class PlayerInterface(object):
    def __init__(self, exe, default_args):
        self.exe = exe
        self.default_args = default_args

    def play(self, filepath):
        raise NotImplementedError()


class MPlayer(PlayerInterface):
    def play(self, filepath):
        cmd = [self.exe] + self.default_args + [filepath]
        subprocess.Popen(cmd)


class OmxPlayer(PlayerInterface):
    pass


class VlcPlayer(PlayerInterface):
    def play(self, filepath):
        cmd = [self.exe] + self.default_args + [filepath.resolve().as_uri()]
        subprocess.Popen(cmd)
