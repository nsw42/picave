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
        super().__init__(exe, default_args)
        self.child = None

    def play(self, filepath):
        cmd = [self.exe] + self.default_args + [filepath]
        self.child = subprocess.Popen(cmd,
                                      stdin=subprocess.DEVNULL,
                                      stdout=subprocess.DEVNULL,
                                      stderr=subprocess.DEVNULL)


class Mpg123(PlayerInterface):
    # nothing needed - default behaviour is fine
    def play(self, filepath):
        cmd = [self.exe] + self.default_args + [filepath.resolve()]
        self.child = subprocess.Popen(cmd,
                                      stdin=subprocess.DEVNULL,
                                      stdout=subprocess.DEVNULL,
                                      stderr=subprocess.DEVNULL)


class MPVPlayer(PlayerInterface):
    # nothing needed - default behaviour is fine
    pass


class OmxPlayer(PlayerInterface):
    # nothing needed - default behaviour is fine
    pass


class VlcPlayer(PlayerInterface):
    def play(self, filepath):
        cmd = [self.exe] + self.default_args + [filepath.resolve().as_uri()]
        subprocess.Popen(cmd)
