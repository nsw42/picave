# PiCave

A Raspberry Pi-powered Personal Trainer for cyclists

(Cyclists often call their turbo trainer setup their 'pain cave' - hence the project name)

See <https://www.picave.org> for the main website.

See [docs/setup.md](docs/setup.md) for the quick summary of how to set up a Raspberry Pi to run this.

See [docs/development.md](docs/development.md) for info about getting set up to contribute to development.

## Version history

* v1.1.0: Major functionality enhancements:
    * Add support for per-video target power, as a substitute for properly personalised training
    * Store and show favourite videos, including the ability to show *only* favourites
    * Add a profile (=configuration file) chooser dialog
    * Add a configuration editor dialog
    * Add a quit/shutdown dialog
    * Add command-line arguments to control whether to:
        a) show the profile chooser
        a) include a 1m delay when shutting down (useful for development, but often annoying in normal use)
        a) hide the mouse pointer
        a) go to full screen when running
    * Simplify configuration file format
        * *NB* This is change is backwards incompatible: config files must be updated before running the new version
    * Improve support for the OSMC remote control
    * Improve video playback:
        * Better omxplayer support, using the omxplayer.player Python library
        * Add support for libvlc for control
        * Support play/pause
    * Switch to json5 to allow for comments in hand-written config files
* v1.0.0: First version
