import json
import logging
import os
import pathlib
import shutil
import sys

import jsonschema

from players import PlayerLookup


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
    if ext == '.mp3':
        return first_available_player(['mpg123', 'mplayer', 'mpv'])
    elif ext == '.mp4' or ext == '.mkv':
        return first_available_player(['omxplayer', 'mpv', 'vlc'])
    else:
        assert False, "Missing default player for " + ext


def default_config_path():
    return pathlib.Path.home() / '.picaverc'


def first_available_player(binaries):
    for binary in binaries:
        path = default_binary(binary)
        if path:
            return binary
    return None


class Config(object):
    def __init__(self, filename=None):
        self.executables = {}  # map from executable name to pathlib.Path
        self.players = {}  # map from '.ext' to Player instance
        self.warm_up_music_directory = None  # pathlib.Path
        self.video_cache_directory = None  # pathlib.Path
        self.ftp = None  # number
        self.favourites = []  # list of video ids (str)

        schema_filename = pathlib.Path(__file__).parent / 'config.schema.json'
        self.schema = json.load(open(schema_filename))
        self.executable_names = (self.schema['definitions']['supported_players']['enum']
                                 + self.schema['definitions']['other_executables']['enum'])

        if filename:
            self._init_from_file(filename)
            self.filename = filename
        else:
            self._init_with_defaults()
            self.filename = default_config_path()

    def _init_from_file(self, filename):
        try:
            handle = open(filename)
        except OSError:
            # TODO: Error handling
            raise
        json_content = json.load(handle)
        jsonschema.validate(instance=json_content, schema=self.schema)  # throws on validation error

        for binary in self.executable_names:
            self.executables[binary] = config_binary(json_content, binary)
            logging.debug("Exe %s=%s" % (binary, self.executables[binary]))

        for player_config in json_content['filetypes']:
            ext = player_config['ext']
            player = player_config['player']
            cmd_args = player_config.get('options', None)
            player_parameters = player_config.get('parameters', {})
            player_class = PlayerLookup[player]
            self.players[ext] = player_class(exe=self.executables[player],
                                             default_args=cmd_args,
                                             player_parameters=player_parameters)
            logging.debug("player %s=%s" % (ext, self.players[ext]))

        self.video_cache_directory = pathlib.Path(json_content['video_cache_directory']).expanduser().resolve()

        warm_up_dir = json_content.get('warm_up_music_directory')
        if warm_up_dir:
            self.warm_up_music_directory = pathlib.Path(warm_up_dir).expanduser().resolve()
        else:
            self.warm_up_music_directory = None

        self.ftp = json_content['FTP']
        self.favourites = json_content['Favourites']

    def _init_with_defaults(self):
        self.video_cache_directory = pathlib.Path('~/.picave_cache').expanduser()
        if not self.video_cache_directory.exists():
            self.video_cache_directory.mkdir()

        for binary in self.executable_names:
            self.executables[binary] = default_binary(binary)
            logging.debug("Exe %s=%s" % (binary, self.executables[binary]))

        for ext in self.schema['definitions']['player']['properties']['ext']['enum']:
            player_name = default_player(ext)
            player_class = self.player_lookup[player_name]
            player = player_class(exe=self.executables[player_name], default_args=None)
            self.players[ext] = player
            if player is None:
                logging.warning("No player found for %s files" % ext)
            else:
                logging.debug("player %s=%s" % (ext, self.players[ext]))

        self.ftp = 200
        self.favourites = []

    def save(self):
        to_write = {
            'video_cache_directory': str(self.video_cache_directory),
            'warm_up_music_directory': str(self.warm_up_music_directory),
            'executables': [{
                "name": name,
                "path": str(path)
            } for name, path in self.executables.items()],
            'filetypes': [{
                "ext": ext,
                "player": player.name,
                "options": player.default_args,
                "parameters": player.player_parameters
            } for ext, player in self.players.items()],
            'FTP': self.ftp,
            'Favourites': self.favourites
        }
        temp_filename = self.filename.with_suffix('.new')
        if temp_filename.exists():
            os.remove(temp_filename)
        with open(temp_filename, 'w') as handle:
            json.dump(to_write, handle, indent=4)

        if self.filename.exists():
            backup_filename = self.filename.with_suffix('.bak')
            if backup_filename.exists():
                os.remove(backup_filename)
            os.rename(self.filename, backup_filename)
        os.rename(temp_filename, self.filename)
