# Setting up your development environment on a non-Raspberry Pi OS Linux machine

## Install dependencies

Use your OS package manager to install programs as follows:

|      *Component*      |  *Alpine Linux*  |  *Debian/Ubuntu*  |  *Notes*  |
| go compiler           |       `go`       |      `golang`     |  The OS has old versions: picave is built with go 1.22. You'll probably need to install go from <https://go.dev/doc/install>  |
| libgtk libraries      |     `gtk4.0`     |    `libgtk-4-1`   | Note the Alpine package is in the `community` repository, which you might need to enable |
| a music player        |     `mpg123`     |      `mpg123`     |  |
| a video player        |      `mpv`       |       `mpv`       |  |
| a YouTube downloader  |     `yt-dlp`     |      `yt-dlp`     |  |
| git tools             |      `git`       |       `git`       |  |

## Fetch the source

```bash
git clone https://github.com/nsw42/picave.git
cd picave
```

## Try running it

```bash
go run .
```

Note that this stage may take a while the first time you do so: building the go bindings to GTK4 takes several minutes.
