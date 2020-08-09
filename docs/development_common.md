# Setting up your development environment - steps common to all platforms

## (Recommended) Set up python version virtualenv

* install [pyenv](https://github.com/pyenv/pyenv#installation) - the [pyenv installer](https://github.com/pyenv/pyenv-installer) is recommended
* if not done via the pyenv installer: install [pyenv virtualenv](https://github.com/pyenv/pyenv-virtualenv)
* If you have an appropriate python version already (like the Pi)
  * install [pyenv register](https://github.com/doloopwhile/pyenv-register)
  * register the system python3: `pyenv register /usr/bin/python3.7`
  * (NB. 2020-06-20: This didn't work. Resorted to alternative, below)
* Otherwise build and installl an appropriate version
  * Install build prerequisites as per the Ubuntu/Debian section in <https://github.com/pyenv/pyenv/wiki/Common-build-problems>
  * `pyenv install 3.7.3` (or newer)
* Create a virtualenv for development: `pyenv virtualenv system-3.7.3 picave` or `pyenv virtualenv 3.7.3 picave` depending on where your python came from
  * Note this may need updating, depending on Raspbian python version

## Fetch the code

* `git clone https://github.com/nsw42/picave.git`
* `cd picave`

## Start editing

* `code-oss .`
  * Install the python extension
  * Select the appropriate Python version
