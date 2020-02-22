# Development


## Pre-requisites

* Completed setup.md steps

## References

* <https://www.codementor.io/@princerapa/python-media-player-vlc-gtk-favehuy2b>

## Set up development environment (R-Pi)

### (Optional) Install Visual Studio Code

See, for instance, <https://pimylifeup.com/raspberry-pi-visual-studio-code/>

### (Optional) Install gvim

`sudo apt-get install vim-gtk3`

### Set up the python virtualenv

See below

### Install dependencies

* `pip install python-vlc`



## Set up development environment (macOS)

### Set up the python virtualenv

See below

### Install dependencies

* Install pygobject: See <https://pygobject.readthedocs.io/en/latest/getting_started.html#macosx-getting-started>
    * Note that this didn't play nice with my virtualenv, and I ended up kludging it:

```sh
for d in /usr/local/Cellar/pygobject3/3.34.0/lib/python3.7/site-packages/*; do   
  ln -s $d ~/.pyenv/versions/picave/lib/python3.7/site-packages/`basename $d`;
done
```
* `pip install python-vlc`


## (Recommended) Set up python version virtualenv

* install [pyenv](https://github.com/pyenv/pyenv#installation)
* install [pyenv virtualenv](https://github.com/pyenv/pyenv-virtualenv)
* If you have an appropriate python version already (like the Pi)
    * install [pyenv register](https://github.com/doloopwhile/pyenv-register)
    * register the system python3: `pyenv register /usr/bin/python3.7`
* Otherwise build and installl an appropriate version
    * `pyenv install 3.7.3`
        * You can use later without problems
* Create a virtualenv for development: `pyenv virtualenv system-3.7.3 picave`
    * Note this may need updating, depending on Raspbian python version


## Fetch the code

* `git clone ssh://neil@192.168.0.1/opt/git/picave.git`
  * Will need updating when this moves to github
* `cd picave`


## Start editing

* `code-oss .`
    * Install the python extension
    * Select the appropriate Python version


