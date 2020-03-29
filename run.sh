#! /bin/bash

export PYENV_ROOT=/home/pi/.pyenv

eval "$($PYENV_ROOT/bin/pyenv init -)"
eval "$($PYENV_ROOT/bin/pyenv virtualenv-init -)"

cd $(dirname "$0")/src
export > ../run.log
python main.py --wait-for-media --debug >> ../run.log 2>&1
