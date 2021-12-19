# Setting up your development environment on macOS

## Set up the python virtualenv

See [development_common.md](development_common.md) <!-- TODO: Add anchor to this link -->

## Install platform-specific dependencies

* Install pygobject: See <https://pygobject.readthedocs.io/en/latest/getting_started.html#macosx-getting-started>
  * At time of writing, if you already have Homebrew installed, this says simply: `brew install pygobject3 gtk+3`
  * Note that this didn't play nice with my virtualenv, and I ended up kludging it:

    ```sh
    for d in /usr/local/Cellar/pygobject3/3.34.0/lib/python3.7/site-packages/*; do
      ln -s $d ~/.pyenv/versions/picave/lib/python3.7/site-packages/`basename $d`;
    done
    ```

    or, with newer Homebrew and Python:

    ```sh
    for d in /opt/homebrew/Cellar/pygobject3/3.42.0_1/lib/python3.9/site-packages/*; do
      ln -s $d ~/.pyenv/versions/picave/lib/python3.9/site-packages/`basename $d`;
    done
    ```

  * Note that this didn't install default icons. `brew install adwaita-icon-theme` did install them.
    I initially thought I needed to add an explicit search path to find them, but that doesn't
    seem necessary any more.
  * `brew install gstreamer`
  * `brew install gst-plugins-base`
  * `brew install gst-plugins-good`
  * `brew install gst-libav`

### Install common dependencies

See [development_common.md](development_common.md) <!-- TODO: Add anchor to this link -->

### Optional additional components

* `brew install mpg123` gives one of the better players from a control point of view

## macOS specific notes

* On an M1 MacBook Pro, am experiencing segfaults when closing a window
