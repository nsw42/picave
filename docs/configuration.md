# Configuration

A configuration file can be specified using the `-c` / `--command` command line argument. `~/.picaverc` is the default file if no argument is specified.

## Selecting players for filetypes

PiCave has support for different media players according to what works well on your platform.  `omxplayer` is probably the best choice for a Raspberry Pi, but [mplayer](www.mplayerhq.hu), [mpg123](www.mpg123.de), [mpv](mpv.io) and [VLC](www.videolan.org) are supported to varying degrees. VLC can be used either as a standalone sub-process, by setting the player to `vlc`; or to play video embedded in the PiCave window (which looks tidier, but loses some of the flexibility of VLC) by setting the player to `libvlc`.

## Video position

Seting player for a filetype to `omxplayer` or `libvlc` will play the video properly embedded in the PiCave window. Other video players (`mplayer`, `mpv`, `vlc`) attempt to simulate this by starting the application over the top of the PiCave window, but the effect is not as smooth as with `omxplayer`/`libvlc`.

### omxplayer video position

If using `omxplayer` on the Raspberry Pi and the video is misaligned, it's probably due to video underscan or overscan.  The `parameters` block of the appropriate `filetypes` section of the configuration file allows the video position to be adjusted:

```json
{
    ...
    "filetypes": [
        ...
        {
            "ext": ".mp4",
            "player": "omxplayer",
            "parameters": {
                "margin_left": 48,
                "margin_right": 48,
                "margin_top": 48,
                "margin_bottom": 48
            }
        }
        ...
    ]
}

```
