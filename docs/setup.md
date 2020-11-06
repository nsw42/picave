# Setup

Largely, you just need to follow this bullet point list top-to-bottom. There are two main variants summarised: one using the Raspberry Pi NOOBS SD card that comes with a starter kit; the other for manually preparing the OS SD card. Which of those two options you're following will matter at a few points along the way.

## Equipment

* Raspberry Pi 3 Model B starter kit or a Raspberry Pi 4 Model B (4GB) (heatsink recommended if using a case)
* USB keyboard
* USB mouse
* USB storage device (e.g. 128GB) if not using a high capacity SD card
* Optional: Remote control: <https://osmc.tv/store/product/osmc-remote-control/>

### Manually preparing the OS SD card

If not using NOOBS, as of 2020-06-20:

* Download 'Raspberry Pi OS (32-bit) with desktop' at <https://downloads.raspberrypi.org/raspios_armhf_latest>
* Unzip
* Download, install run [balenaEtcher](https://www.balena.io/etcher/)
* Put SD card in adapter and plug in to computer USB
* Select 'Flash from file', select the unzipped image; select target device; start
* Wait while it flashes and verifies

## Connect the R-Pi hardware

* Apply the heatsink (if you're using one)
* Put the Pi into its case
* Plug in the micro-USB with OS
* Connect USB keyboard and mouse
* If using, connect USB external storage (R-Pi 4: use one of the USB 3 slots for the storage device)
* If using, connect the USB receiver for the remote control
* Connect HDMI cable
* Turn on TV
* Apply power to the R-Pi

## Install/Configure OS

### If using NOOBS

(As of 2019, probably slightly different now that the OS has been renamed)

* Configure wifi from Noobs menu
* Select "Raspbian [RECOMMENDED]" to install via wifi
* Click OK, Pi reboots, Raspbian boots
* Go through Raspbian setup wizard
* Install OS updates and reboot

### Otherwise

* Go through the installation wizard
* Ensure all OS software is up-to-date
    * See https://www.raspberrypi.org/documentation/raspbian/updating.md if the automatic update fails
    * `sudo apt autoremove` at the end can prevent warnings on future `apt` commands


## Install additional software

* `sudo apt remove youtube-dl`
* `sudo apt install mpg123`
* `sudo apt install python3-gi-cairo`
* Install youtube-dl as per <https://ytdl-org.github.io/youtube-dl/download.html>
    * and check that it works by downloading a random short YouTube video
* `git clone https://github.com/nsw42/picave.git`
* Set up a python environment. For now, see [development_common.md](development_common.md)
* `cd picave`
* `pip install jsonschema`
* `pip install mutagen`
* `pip install python-vlc`
* `pip install requests`
* `sudo apt install omxplayer`
* `sudo apt install libdbus-glib-1-dev`
* `sudo apt install libgirepository1.0-dev`
* `sudo apt install libcairo2-dev`
* `sudo apt install sudo apt install libgirepository1.0-dev`
* `pip install wheel`
* `pip install omxplayer-wrapper`
* `pip install pycairo`
* `pip install PyGObject`

## Set your preferences

* `vi ~/.picaverc` to create a config file that looks like this:

```json
{
    "video_cache_directory": "/your/path/here",
    "warm_up_music_directory": "/your/path/here",
    "executables": [
        {
            "name": "youtube-dl",
            "path": "/usr/local/bin/youtube-dl"
        }
    ],
    "filetypes": [
        {
            "ext": ".mp3",
            "player": "mpg123",
            "options": ["--quiet"]
        },
        {
            "ext": ".mp4",
            "player": "omxplayer"
        },
        {
            "ext": ".mkv",
            "player": "omxplayer"
        }
    ],
    "FTP": {
        "default": 250
    }
}
```

## Check that everything runs correctly

```bash
cd picave
./run.sh
```

If anything looks wrong, have a look through `run.log`.

## Set to run at boot

```bash
cd deployment
sudo ./install.sh
```

## To remove the autostart at boot

```bash
cd deployment
sudo ./uninstall.sh
```
