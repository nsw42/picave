import json
import logging
import pathlib
import shutil
import sys

import jsonschema

from players import Mpg123, MPlayer, MPVPlayer, OmxPlayer, VlcPlayer


def config_binary(json_content, binary):
    for config_binary in json_content.get('executables', {}):
        if config_binary['name'] == binary:
            return pathlib.Path(config_binary['path'])
    return default_binary(binary)


def default_binary(binary):
    # binary not explicitly found: can we find it on the path?
    path = shutil.which(binary)
    if path:
        return pathlib.Path(path)
    # Special-case defaults?
    if sys.platform == 'darwin' and binary == 'vlc':
        path = pathlib.Path('/Applications/VLC.app/Contents/MacOS/VLC')
        if path.exists():
            return path
    return None


def default_player(ext):
    # TODO: Will need something more clever than this...
    return default_binary('mpv')


class Config(object):
    def __init__(self, filename=None):
        self.executables = {}  # map from executable name to pathlib.Path
        self.players = {}  # map from '.ext' to Player instance
        self.warm_up_music_directory = None  # pathlib.Path
        self.video_cache_directory = None  # pathlib.Path

        schema_filename = pathlib.Path(__file__).parent / 'config.schema.json'
        self.schema = json.load(open(schema_filename))

        if filename:
            self._init_from_file(filename)
        else:
            self._init_with_defaults()

    def _init_from_file(self, filename):
        try:
            handle = open(filename)
        except OSError:
            # TODO: Error handling
            raise
        json_content = json.load(handle)
        jsonschema.validate(instance=json_content, schema=self.schema)  # throws on validation error

        binaries = (self.schema['definitions']['supported_players']['enum']
                    + self.schema['definitions']['other_executables']['enum'])
        for binary in binaries:
            self.executables[binary] = config_binary(json_content, binary)
            logging.debug("Exe %s=%s" % (binary, self.executables[binary]))

        player_lookup = {
            'mpg123': Mpg123,
            'mplayer': MPlayer,
            'mpv': MPVPlayer,
            'omxplayer': OmxPlayer,
            'vlc': VlcPlayer
        }
        for player_config in json_content['filetypes']:
            ext = player_config['ext']
            player = player_config['player']
            cmd_args = player_config.get('options', [])
            player_class = player_lookup[player]
            self.players[ext] = player_class(self.executables[player], cmd_args)
            logging.debug("player %s=%s" % (ext, self.players[ext]))

        self.video_cache_directory = pathlib.Path(json_content['video_cache_directory']).expanduser().resolve()
        if not self.video_cache_directory.is_dir():
            # TODO: Use a proper exception type
            raise Exception('Video cache directory does not exist or is not a directory')

        warm_up_dir = json_content.get('warm_up_music_directory')
        if warm_up_dir:
            self.warm_up_music_directory = pathlib.Path(warm_up_dir).expanduser().resolve()
            if not self.warm_up_music_directory.is_dir():
                logging.warning('Warm up music directory does not exist or is not a directory')
                self.warm_up_music_directory = None
        else:
            self.warm_up_music_directory = None

    def _init_with_defaults(self):
        self.video_cache_directory = pathlib.Path('~/.picave_cache').expanduser()
        if not self.video_cache_directory.exists():
            self.video_cache_directory.mkdir()

        for ext in self.schema['definitions']['player']['properties']['ext']['enum']:
            self.players[ext] = default_player(ext)

        for binary in self.schema['definitions']['executable']['properties']['name']['enum']:
            self.executables[binary] = default_binary(binary)
