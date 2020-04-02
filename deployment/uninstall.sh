#! /bin/bash

AUTOSTART_FILE=/etc/xdg/lxsession/LXDE-pi/autostart
AUTOSTART_TMP=/tmp/autostart

grep -v picave $AUTOSTART_FILE > $AUTOSTART_TMP
# next line will require root
mv -f $AUTOSTART_TMP $AUTOSTART_FILE
