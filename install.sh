#!/bin/bash
# Copyright (c) 2019 Greg Crist
# Licensed under the MIT License

# Description
# Installs the wifi roaming service

if [ $EUID != 0 ]; then
    echo "Must be run as root!"
    exit 1
fi

# set to false to just to a test-installation
LIVERUN=true


APP_SRC="src"
APP_DEST="/usr/local/wifi-roaming"
SYSTEMD_SRC="ext"
SYSTEMD_DEST="/lib/systemd/system"

declare -a REQ_PACKAGES
REQ_PACKAGES=( python-daemonize python-pyparsing )

declare -a SRC_FILES
SRC_FILES=( wifi-roaming.py wpa.py )

declare -a SVC_FILES
SVC_FILES=( wifi-roaming.service )

echo "Installing required packages"
for PKG in ${REQ_PACKAGES[*]}; do
    echo "  Installing package: $PKG..."
    $LIVERUN && apt-get -y install $PKG
done

echo "Creating destination directory '$APP_DEST'"
$LIVERUN && mkdir -p $APP_DEST
if [ $? -ne 0 ]; then
    $LIVERUN && echo "Error creating directory '$APP_DEST'"
fi

echo "Installing source files into destination directory"
for FILE in ${SRC_FILES[*]}; do
    echo "  Copying $FILE to $APP_DEST/$FILE"
    $LIVERUN && cp -r $APP_SRC/$FILE $APP_DEST/$FILE
    if [ $? -ne 0 ]; then
        $LIVERUN && echo "Unable to copy $FILE to $APP_DEST/$FILE"
    fi
done

echo "Installing and enabling service files"
for SVC in ${SVC_FILES[*]}; do
    echo "  Copying $SVC"
    $LIVERUN && cp -r $SYSTEMD_SRC/$SVC $SYSTEMD_DEST/$SVC
    if [ $? -ne 0 ]; then
        $LIVERUN && echo "Unable to copy $SVC to $SYSTEMD_DEST/$FILE"
    fi

    echo "  Enabling $SVC"
    $LIVERUN && systemctl enable $SVC
    if [ $? -ne 0 ]; then
        $LIVERUN && echo "Unable to enable service $SVC"
    fi
done

echo "Run 'systemctl start wifi-roaming.service' to start the service"

