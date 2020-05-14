# Setup

## Equipment

* Raspberry Pi 3 Model B starter kit
* USB keyboard
* USB mouse
* USB storage device (128GB)

## Connect the R-Pi hardware

* Put the Pi into its case
* Plug in the micro-USB with software
* Connect USB keyboard and mouse
* Connect HDMI cable
* Turn on TV
* Apply power to Pi

## Install OS

* Configure wifi from Noobs menu
* Select "Raspbian [RECOMMENDED]" to install via wifi
* Click OK, Pi reboots, Raspbian boots
* Go through Raspbian setup wizard
* Install OS updates and reboot

## Install additional software

* `sudo apt remove youtube-dl`
* `sudo apt install mpg123`
* `sudo apt install python3-gi-cairo`
* Install youtube-dl as per <https://ytdl-org.github.io/youtube-dl/download.html>
* `pip install jsonschema`
* `pip install mutagen`
* `pip install python-vlc`
* `pip install requests`
* `pip install omxplayer-wrapper`

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
