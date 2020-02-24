# Setting up your development environment - steps common to all platforms

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

## Install common dependencies

* `pip install python-vlc`
* `pip install requests`
* `pip install jsonschema`

## Fetch the code

* `git clone ssh://neil@192.168.0.1/opt/git/picave.git`
  * Will need updating when this moves to github
* `cd picave`


## Start editing

* `code-oss .`
    * Install the python extension
    * Select the appropriate Python version
