class PlayerInterface(object):
    def play(self, filepath):
        raise NotImplementedError()


class MPlayer(PlayerInterface):
    pass


class OmxPlayer(PlayerInterface):
    pass


class VlcPlayer(PlayerInterface):
    pass
