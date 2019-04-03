# Wifi Roaming Service

## Description

The Wifi Roaming Service will detect configured networks and disconnect/connect automatically based upon priority. This was created to solve the problem of a raspbery pi roaming between a mobile hotspot installed in a car and home wifi, but can be useful in a variety of other situations.

## Installation
To install, run as root:
```
sudo install.sh
```

The service will be enabled to run at startup. To start the service after installing, run:
```
systemctl start wifi-roaming.service
```

## Configuration
Configuration is simply re-used from wpa\_supplicant.conf. The key fields that must be specified for each network are:
 * ssid
 * priority

Networks will be connected in order of the highest 'priority'

Sample Configuration:
```
network={
        ssid="pi-wifi-1"
        psk="pi1234"
        priority=255
        scan_ssid=1
}

network={
        ssid="pi-wifi-2"
        psk="pi5678"
        priority=1000
        scan_ssid=1
}

network={
        ssid="guest-wifi"
        psk="guest"
        priority=1
        scan_ssid=1
}
```
