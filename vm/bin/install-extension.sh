#!/usr/bin/env bash
set -e

drv_dir="/tmp/weewx-weatherlinklive-driver"

[[ -d "$drv_dir" ]] || sudo mkdir -p "$drv_dir"
sudo cp -r /vagrant/* $drv_dir
sudo wee_extension --install=$drv_dir /etc/weewx/weewx.conf
sudo rm -fr $drv_dir
