from collections import defaultdict
import logging
import os
import pathlib
import shutil
import sys
from typing import Union

import json5
import jsonschema

from players import PlayerLookup


class LoadException(Exception):
    """
    An exception thrown when failing to load/validate a configuration file
    """


def config_binary(json_content, binary):
    executables = json_content.get('executables', {})
    executable = executables.get(binary, {})
    path = executable.get('path') if executable else None
    if path:
        path = pathlib.Path(path)
        if path.exists():
            return path
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
        self.power_levels = defaultdict(dict)  # map from video id (or 'default') to dict ...
        # the inner dict maps 'FTP'/'MAX' to number or string (percent of FTP)
        self.favourites = []  # list of video ids (str)
        self.show_favourites_only = False

        schema_filename = pathlib.Path(__file__).parent / 'config.schema.json'
        self.schema = json5.load(open(schema_filename, encoding='utf-8'))
        self.executable_names = list(self.schema['properties']['executables']['properties'].keys())
        logging.debug(f"Executables: {self.executable_names}")

        if filename:
            try:
                self._init_from_file(filename)
            except jsonschema.exceptions.ValidationError as e:
                raise LoadException(e.message) from e
            self.filename = filename
        else:
            self._init_with_defaults()
            self.filename = default_config_path()

    def _init_from_file(self, filename):
        try:
            handle = open(filename, encoding='utf-8')
        except OSError as e:
            # TODO: Error handling
            raise LoadException(e) from e
        try:
            json_content = json5.load(handle)
        except ValueError as e:
            raise LoadException(e) from e
        jsonschema.validate(instance=json_content, schema=self.schema)  # throws on validation error

        for binary in self.executable_names:
            self.executables[binary] = config_binary(json_content, binary)
            logging.debug(f"Exe {binary}={self.executables[binary]}")

        for ext, player_config in json_content['filetypes'].items():
            player = player_config['player']
            cmd_args = player_config.get('options', None)
            player_parameters = player_config.get('parameters', {})
            self.set_filetype_player(ext, player, cmd_args, player_parameters)
            logging.debug(f"player {ext}={self.players[ext]}")

        self.video_cache_directory = pathlib.Path(json_content['video_cache_directory']).expanduser().resolve()

        warm_up_dir = json_content.get('warm_up_music_directory')
        if warm_up_dir:
            self.warm_up_music_directory = pathlib.Path(warm_up_dir).expanduser().resolve()
        else:
            self.warm_up_music_directory = None

        self.power_levels.update(json_content.get('power_levels', {}))
        if self.get_power('default', 'FTP', expand_default=True) is None:
            logging.warning("Using default values for FTP due to incomplete config")
            self.set_power('default', 'FTP', 200)
        self.favourites = json_content.get('favourites', [])
        self.show_favourites_only = json_content.get('show_favourites_only', False)

    def set_filetype_player(self, ext, player, cmd_args, player_parameters):
        player_class = PlayerLookup.get(player)
        if player_class is None:
            raise LoadException(f"{player} is not a recognised player")
        exe = self.executables[player]
        if not exe:
            exe = default_binary(player)
        self.players[ext] = player_class(exe=exe,
                                         default_args=cmd_args,
                                         player_parameters=player_parameters)

    def _init_with_defaults(self):
        self.video_cache_directory = pathlib.Path('~/.picave_cache').expanduser()
        if not self.video_cache_directory.exists():
            self.video_cache_directory.mkdir()

        for binary in self.executable_names:
            self.executables[binary] = default_binary(binary)
            logging.debug(f"Exe {binary}={self.executables[binary]}")

        for ext in self.schema['properties']['filetypes']['properties']:
            player_name = default_player(ext)
            player_class = PlayerLookup[player_name]
            player = player_class(exe=self.executables[player_name], default_args=None, player_parameters={})
            self.players[ext] = player
            if player is None:
                logging.warning(f"No player found for {ext} files")
            else:
                logging.debug(f"player {ext}={self.players[ext]}")

        self.set_power('default', 'FTP', 200)
        self.favourites = []
        self.show_favourites_only = False

    def save(self):
        to_write = {
            'video_cache_directory': str(self.video_cache_directory),
            'warm_up_music_directory': str(self.warm_up_music_directory),
            'executables': dict([name, {"path": str(path)}] for name, path in self.executables.items() if path),
            'filetypes': dict([ext, {
                "player": player.name,
                "options": player.default_args,
                "parameters": player.player_parameters
            }] for ext, player in self.players.items()),
            'favourites': self.favourites,
            'show_favourites_only': self.show_favourites_only,
            'power_levels': self.power_levels,
        }
        temp_filename = self.filename.with_suffix('.new')
        if temp_filename.exists():
            os.remove(temp_filename)
        with open(temp_filename, 'w', encoding='utf-8') as handle:
            json5.dump(to_write, handle, indent=4)

        if self.filename.exists():
            backup_filename = self.filename.with_suffix('.bak')
            if backup_filename.exists():
                os.remove(backup_filename)
            os.rename(self.filename, backup_filename)
        os.rename(temp_filename, self.filename)

    def get_power(self, video_id: str, ftp_or_max: str, expand_default: bool) -> Union[None, int, str]:
        assert ftp_or_max in ['FTP', 'MAX']
        logging.debug(f'get_power: {video_id}, {self.power_levels}')
        power = self.power_levels[video_id].get(ftp_or_max)
        if expand_default and (video_id != 'default') and (power is None):
            power = self.power_levels['default'].get(ftp_or_max)
        return power

    def set_power(self, video_id: str, ftp_or_max: str, power: Union[None, int, str]):
        assert ftp_or_max in ['FTP', 'MAX']
        if power is None:
            if (video_id in self.power_levels) and (ftp_or_max in self.power_levels[video_id]):
                del self.power_levels[video_id][ftp_or_max]
        else:
            self.power_levels[video_id][ftp_or_max] = power
