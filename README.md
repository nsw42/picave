# PiCave

A Raspberry Pi-powered Personal Trainer for cyclists

(Cyclists often call their turbo trainer setup their 'pain cave' - hence the project name)

See <https://www.picave.org> for the main website.

See [docs/setup.md](docs/setup.md) for the quick summary of how to set up a Raspberry Pi to run this.

See [docs/development.md](docs/development.md) for info about getting set up to contribute to development.

## Version history

* v1.2.0: Minor improvements:
    * It's now possible to set a custom power level for max efforts in a session (as well as the existing behaviour of a custom FTP for a session)
        * *NB* This is another backwards incompatible change: config files must be updated before running the new version
    * Add an (optional) automatic update check when exiting the application
    * Minor improvements to the feed contents
    * Minor bug-fixes to avoid exceptions on unusual (=invalid) config file contents
    * Bug-fixes to avoid odd behaviour if the clock changes during a session (e.g. because the Pi connects to wifi and updates the local time)
    * Bug-fix to ignore subtitles (`.vtt` files) in the video cache
    * Minor layout improvements in the video index window
    * Now requires Python >= v3.6
* v1.1.0: Major functionality enhancements:
    * Add support for per-video target power, as a substitute for properly personalised training
    * Store and show favourite videos, including the ability to show *only* favourites
    * Add a profile (=configuration file) chooser dialog
    * Add a configuration editor dialog
    * Add a quit/shutdown dialog
    * Add command-line arguments to control whether to:
        1. show the profile chooser
        1. include a 1m delay when shutting down (useful for development, but often annoying in normal use)
        1. hide the mouse pointer
        1. go to full screen when running
    * Simplify configuration file format
        * *NB* This change is backwards incompatible: config files must be updated before running the new version
    * Improve support for the OSMC remote control
    * Improve video playback:
        * Better omxplayer support, using the omxplayer.player Python library
        * Add support for libvlc for control
        * Support play/pause
    * Switch to json5 to allow for comments in hand-written config files
* v1.0.0: First version
