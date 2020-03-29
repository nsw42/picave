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

    def play(self, filepath):
        cmd = [self.exe] + self.default_args + [filepath.resolve()]
        self.child = subprocess.Popen(cmd)

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
                                      stdin=subprocess.DEVNULL,
                                      stdout=subprocess.DEVNULL,
                                      stderr=subprocess.DEVNULL)


class Mpg123(PlayerInterface):
    def __init__(self, exe, default_args):
        if default_args is None:
            default_args = ['--quiet']
        super().__init__(exe, default_args)

    def play(self, filepath):
        cmd = [self.exe] + self.default_args + [filepath.resolve()]
        self.child = subprocess.Popen(cmd,
                                      stdin=subprocess.DEVNULL,
                                      stdout=subprocess.DEVNULL,
                                      stderr=subprocess.DEVNULL)


class MPVPlayer(PlayerInterface):
    def __init__(self, exe, default_args):
        if default_args is None:
            default_args = ['--geometry=0:0']
        super().__init__(exe, default_args)


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
