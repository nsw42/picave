# Configuration

All configuration can be achieved through the profile editor window, accessed
from the button on the main window.

A configuration file can be specified using the `-p` / `--profile` command line argument.
`~/.picaverc` is the default file if no argument is specified.

## Selecting players for filetypes

PiCave has support for different media players according to what works well on
your platform.

`omxplayer` is probably the best choice for a Raspberry Pi, but
[mplayer](https://www.mplayerhq.hu), [mpg123](https://www.mpg123.de) and
[mpv](https://mpv.io) are supported to varying degrees.

(The old, Python, version of the program also supported VLC/libvlc; it is
hoped to reintroduce this support to the new version at some point)

## Video position

Seting player for a filetype to `omxplayer` will play the video properly
embedded in the PiCave window. Other video players attempt to simulate this by
starting the application over the top of the PiCave window, but the effect is
not as smooth as with `omxplayer`.

### omxplayer video position

If using `omxplayer` on the Raspberry Pi and the video is misaligned, it's
probably due to video underscan or overscan.  The `parameters` block of the
appropriate `filetypes` section of the configuration file allows the video
position to be adjusted. See the 'omxplayer parameters' section below, for
an example.

## Configuration file syntax reference

The rest of this file serves as a reference if you want/need to edit the
profile file in a text editor.

The file is a JSON object, and has the following top-level elements

```json
{
    "warm_up_music_directory": "/your/path/here",  // See Directories for detail about this element
    "video_cache_directory": "/your/path/here",  // See Directories for detail about this element
    "executables": {},  // See Executables for detail about the content of this object
    "filetypes": { ... },  // See Filetypes for detail about the content of this object
    "FTP": { ... },  // See FTP for detail about the content of this object
    "favourites": [ ... ],  // See Favourites for detail about the content of this array
    "show_favourites_only": true,  // See Show favourites only for detail about this element
}
```

### Directories

The `warm_up_music_directory` and `video_cache_directory` elements in the configuration file specify where PiCave should look for MP3s for the warm-up music and where it should download videos to save them.

### Executables

This sub-section of the configuration specifies the location of various binaries that are needed (or can be used) by PiCave. If no value is given for a binary, PiCave will look on `PATH`.

This object is configured as follows:

```json
{
    "binary_name": {
        "path": { "/your/path/here" }
    },
    // other binaries here if necessary
}
```

The full list of permitted values for `binary_name` is `mpg123`, `mplayer`, `mpv`, `omxplayer`, `libvlc`, `vlc`, `youtube-dl`.

### Filetypes

This sub-section of the configuration specifies which player, and which arguments to use, for each supported filetype.

This object is configured as follows:

```json
{
    ".extension": {
        "player": "chosen_player",
        "options": [
            "list",
            "of",
            "command-line",
            "options"
        ],
        "parameters": {}
    }
    // other extensions here if necessary
}
```

The list of permitted values for `.extension` is `.mp3`, `.mp4` and `.mkv`.

The value for `player` must be one of the supported players (`mpg123`, `mplayer`, `mpv`, `omxplayer`, `libvlc` or `vlc`).

The value for `options` is the list of command-line options to use when launching the application.

The value for `parameters` is an object to tune the behaviour of PiCave when playing this type of file. This is currently only supported for `omxplayer`, as described below.

#### omxplayer parameters

The size and position of the video within the window can be adjusted by specifying a margin in the parameters object. E.g.:

```json
{
    ...
    "filetypes": {
        ".mp4": {
            "player": "omxplayer",
            "parameters": {
                "margin_left": 48,
                "margin_right": 48,
                "margin_top": 48,
                "margin_bottom": 48
            }
        }
        ...
    }
}
```

### FTP

The FTP section of the configuration allows a default FTP value to be set, as well as video-specific FTP values if desired (e.g. because one video better suits your riding style, and you therefore want power targets to be based on a larger FTP).

The FTP section takes the form of name, value pairs, where the name is the video id, and the value is the FTP to use for the corresponding video (an integer).

Note that if the FTP section exists, a value for `default` is mandatory.

For example:

```json
{
    "FTP": {
        "default": 150,
        "yt_ComQQ41XIDk": 250
    }
}
```

### Favourites

The favourites section of the configuration lists the video ids for those videos that have been marked as a favourite. Marking videos as a favourite is achieved by pressing `*` (i.e. shift-8 on your keyboard, or the multiply button on your numeric keyboard) in the video index window, and doing so saves an updated config file.

If you're writing the config file by hand, the favourites value needs to look something like this:

```json
[
    "yt_ComQQ41XIDk",
    "yt_atK5Q5XVI1A"
]
```

### Show favourites only

The `show_favourites_only` value is a boolean (i.e. `true` or `false`) defining whether the video index window shows all videos (`false`), or just those that have been marked as a favourite (`true`).  This can also be toggled at runtime by pressing `c` (or the OSMC remote control 'index' button), and doing so saves an updated config file.
