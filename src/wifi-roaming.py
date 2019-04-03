#!/usr/bin/python
"""
Copyright (c) 2019 Greg Crist
Licensed under the MIT License

Description:
Monitors the existing wireless connection and available networks. If a
network is discovered with a higher priority than the current network, it
will force the current network to be disconnected and to join the higher
priority network.
"""
import wpa
import sys
import time
import logging
import logging.handlers
from daemonize import Daemonize

app_name = "wifi-roaming"
pid_file = "/tmp/{}.pid".format(app_name)

logger = logging.getLogger(app_name)


def main():
    # Set up logging
    logger.setLevel(logging.INFO)

    # Log to stdout since systemd will catch it
    handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(handler)

    # Daemonize the program to run in the background
    daemon = Daemonize(app=app_name, pid=pid_file, action=wifi_monitor)
    daemon.start()


def wifi_monitor():
    # Constant values
    ignore_wait = 60
    scan_wait   = 10

    # Initial values
    current_network = wpa.get_current_network()
    active_network = {}
    ignore_network  = {}
    ignore_timer = 0
    reassociate = False

    if current_network.get('ssid') != None:
        logger.info("Current network is '{}' with priority {}".format(current_network.get('ssid'), current_network.get('priority', 0)))

    while True:
        # Scan for available networks
        wpa.scan_networks()
        time.sleep(scan_wait)

        active_network = wpa.get_current_network()
        if active_network.get('ssid') != current_network.get('ssid'):
            # To prevent flapping between networks, ignore the "old" current network for a period of time
            ignore_network = current_network
            ignore_timer = time.time()

            if active_network.get('ssid') == None:
                # This should result in the wireless subsystem re-associating on its own
                logger.info("Current network '{}' has gone away".format(current_network.get('ssid')))
            else:
                # The wireless network has actually changed
                logger.info("Current network has changed from '{}' to '{}'".format(
                    current_network.get('ssid'), active_network.get('ssid')))

                current_network = active_network
                continue
        elif time.time() - ignore_timer > ignore_wait:
            # We can stop ignoring the previously ignored network now
            ignore_network = {}

        # Get available network, configured networks, and get the intersection between the two lists based upon the SSID
        available_networks = wpa.get_available_networks()
        configured_networks = wpa.get_configured_networks();

        interested_networks = [ c for c in configured_networks for a in available_networks if c.get('ssid') == a.get('ssid') ]

        for network in interested_networks:
            # Make sure that the network is enabled to allow roaming to it
            wpa.enable_network(network)

            # This network should be ignored
            if network.get('ssid') == ignore_network.get('ssid'):
                continue

            # Force a network reassociation to this network
            if (reassociate == True) or (reassociate == False and network.get('priority', 0) > current_network.get('priority', 0)):
                if network.get('ssid') != current_network.get('ssid'):
                    logger.info("Switching to network '{}' with priority {} from network '{}' with priority {}".format(
                        network.get('ssid'), network.get('priority', 0),
                        current_network.get('ssid'), current_network.get('priority', 0)))

                    if wpa.select_network(network) != True:
                        logger.error("Error: unable to select network '{}'".format(network.get('ssid')))

                reassociate = False
                break

        if current_network.get('ssid') not in [ i.get('ssid') for i in interested_networks ]:
            logger.info("Network '{}' no longer available".format(current_network.get('ssid')))

            # When the next loop through interested networks occurs, automatically associate with the first network
            reassociate = True
            continue

if __name__ == "__main__":
    main()
