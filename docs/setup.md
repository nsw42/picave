# Setup for Raspberry Pi

Largely, you just need to follow this bullet point list top-to-bottom. There are two main variants summarised: one using the Raspberry Pi NOOBS SD card that comes with a starter kit; the other for manually preparing the OS SD card. Which of those two options you're following will matter at a few points along the way.

## Equipment

* Raspberry Pi 3 Model B starter kit or newer (heatsink recommended if using a case with a Raspberry PI 4 in a case, and (from what I've read) active cooling is likely to be necessary with a Raspbery Pi 5)
* USB keyboard
* USB mouse
* USB storage device (64GB+ recommended) if not using a high capacity SD card
* Optional: Remote control: <https://osmc.tv/store/product/osmc-remote-control/>

### Manually preparing the OS SD card

If you're using the NOOBS SD card, you can skip this section. Otherwise, as of 2024-02-03:

* Download 'Raspberry Pi OS (32-bit) with desktop' at <https://downloads.raspberrypi.org/raspios_armhf_latest> or 'Raspberry Pi OS (64-bit) with desktop' at <https://downloads.raspberrypi.org/raspios_arm64_latest>. (If you're going to be using the pre-built binaries, then either will work, and it doesn't really matter which you choose, but you will need to remember which you choose. If you are possibly going to try to build the software from source, be sure to get the 64-bit version.)
* Unzip
* Download, install and run [balenaEtcher](https://www.balena.io/etcher/) or the [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
* Put SD card in adapter and plug in to computer USB
* Select 'Flash from file', select the unzipped image; select target device; start
* Wait while it flashes and verifies

## Connect the R-Pi hardware

* Apply the heatsink (if you're using one)
* Put the Pi into its case
* Plug in the micro-USB with OS
* Connect USB keyboard and mouse
* If using, connect USB external storage (R-Pi 4+: use one of the USB 3 slots for the storage device)
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
    * See <https://www.raspberrypi.com/documentation/computers/os.html> if the automatic update fails
    * `sudo apt autoremove` at the end can prevent warnings on future `apt` commands

## Install additional software

* `sudo apt install mpg123`
* `sudo apt install omxplayer`
* `sudo apt install libgtk-4-1`

## Fetch the picave binary

Depending on which version of the OS you installed, either download <https://picave.org/download/armhf_latest> or <https://picave.org/download/arm64_latest>.

You'll then also need to:

```bash
chmod +x ./picave
```

## Check that everything runs correctly

```bash
./picave
```

If it fails to start, it could be there's another package necessary. Or, maybe
the binary you've downloaded is for the wrong OS - double check armhf vs
arm64. If you run `./picave --help` and see some sensible output, then that
means that you have the right file for your OS.

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
