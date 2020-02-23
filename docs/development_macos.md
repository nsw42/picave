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
    * Note that this didn't install default icons, and `brew install adwaita-icon-theme` didn't help

### Install common dependencies

See [development_common.md](development_common.md) <!-- TODO: Add anchor to this link -->