#! /bin/bash

AUTOSTART_FILE=/etc/xdg/lxsession/LXDE-pi/autostart
AUTOSTART_TMP=/tmp/autostart

RUN_SH=$(realpath $(dirname $0)/../run.sh)

(grep -v picave $AUTOSTART_FILE; echo "@bash $RUN_SH") > $AUTOSTART_TMP
# next line will require root
mv -f $AUTOSTART_TMP $AUTOSTART_FILE
