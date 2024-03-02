# Setting up your development environment for a Raspberry Pi

**These instructions are untested. Since switching to go, the Raspberry Pi binaries have been cross-compiled**

**You will need a Raspberry Pi with at least 2GB of RAM**

## Pre-requisites

* Completed [setup.md](setup.md) steps

## (Optional) Install Visual Studio Code

See, for instance, <https://pimylifeup.com/raspberry-pi-visual-studio-code/>

## (Optional) Install gvim

`sudo apt-get install vim-gtk3`

## Install a go compiler

Go to <https://go.dev/dl/>, download and install the `go1.22.0.linux-arm64.tar.gz` pre-built binary.

## Fetch the source

```bash
git clone https://github.com/nsw42/picave.git
cd picave
```

## Try running it

```bash
go run .
```

Note that this stage may take a very long time the first time you do so:
building the [gotk4 bindings](https://github.com/diamondburned/gotk4/) took
over an hour when I tried it on a Raspberry Pi 3 B+. Expect it to take quite a
while even on the newest Raspberry Pi 5. And, this is the step that requires
at least 2GB RAM.
