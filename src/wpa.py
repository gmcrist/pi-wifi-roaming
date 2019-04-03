#!/usr/bin/python
"""
Copyright (c) 2019 Greg Crist
Licensed under the MIT License

Description:
Provides a simple interface to wpa supplicant
"""

from pyparsing import *
from subprocess import Popen, PIPE
import shlex, time

class WpaSupplicantParser(object):
    """
    A class that parses wpa_supplicant configuration with pyparsing
    """

    # constants
    left_bracket = Literal("{").suppress()
    right_bracket = Literal("}").suppress()
    space = White().suppress()
    modifier = Literal("=").suppress()

    network = Literal("network")

    integer_value = Word(nums).setParseAction(lambda t:int(t[0]))
    string_value = CharsNotIn("{}\n").addParseAction(removeQuotes)

    key = Word(alphanums + "_")
    value = (integer_value | string_value)

    # rules
    assignment = Dict(
        delimitedList(
            Group( key + Optional(space) + modifier + Optional(space) + value ),
            delim = '='
        )
    )

    networkblock = Forward()
    subblock = Forward()

    networkblock << Group(
        (network + ZeroOrMore(space) + modifier + SkipTo("{").suppress())
        + left_bracket
        + subblock
        + right_bracket
    )

    subblock << Group(ZeroOrMore(
        assignment
    ))

    script = (OneOrMore(assignment | networkblock)).ignore(pythonStyleComment)

    def __init__(self):
        # Do something?
        return

    def parse(self, source):
        return self.script.parseString(source)

class WpaCli(object):
    """
    A class that acts as an interface to wpa_cli
    """
    def __init__(self):
        # Do something?
        return

    def _run_cmd_single(self, cmd):
        """
        Execute the external command and get its exitcode, stdout and stderr.
        """
        args = shlex.split(cmd)

        proc = Popen(args, stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        exitcode = proc.returncode

        return exitcode, out, err

    def _run_cmd(self, cmd):
        """Runs the given command locally and returns the output, err and exit_code."""
        if "|" in cmd:
            parts = cmd.split('|')
        else:
            parts = []
            parts.append(cmd)

        i = 0
        p = {}

        for part in parts:
            part = part.strip()

            if i == 0:
                p[i]=Popen(shlex.split(part), stdin=None, stdout=PIPE, stderr=PIPE)
            else:
                p[i]=Popen(shlex.split(part), stdin=p[i-1].stdout, stdout=PIPE, stderr=PIPE)

            i += 1

        (out, err) = p[i-1].communicate()
        exit_code = p[0].wait()

        return exit_code, out, err

    def get_configured_networks(self):
        networks = []

        cmd = "wpa_cli list_networks wlan0 | awk 'NR>2 {print $1, $2}'"
        exit_code, out, err = self._run_cmd(cmd)

        if exit_code != 0:
            return networks

        for network in filter(None, out.split("\n")):
            number, ssid = network.split()

            cmd = "wpa_cli get_network {} priority | awk 'NR>1'".format(number)
            exit_code, out, err = self._run_cmd(cmd)

            if exit_code != 0:
                priority = 0
            else:
                priority = int(out.strip())

            networks.append({'number': int(number), 'ssid': ssid, 'priority': priority})

        return networks

    def get_current_network(self):
        """
        Returns the currently active network
        """

        cmd = "wpa_cli list_networks wlan0 | grep CURRENT | awk '{print $2}'"

        exit_code, out, err = self._run_cmd(cmd)

        if exit_code == 0 and len(out) > 0:
            ssid = out.strip()
        else:
            ssid = None

        return {'ssid': ssid, 'number': -1, 'priority': -1}

    def get_available_networks(self):
	"""
	Returns a list of available networks
	"""
        cmd = "wpa_cli scan_results wlan0 | awk 'NR>2 {print $5}' | sort -u"
        exit_code, out, err = self._run_cmd(cmd)

        if exit_code != 0:
            return []

	networks = sorted(filter(None, out.split("\n")))
	networks = [ {'ssid': network} for network in networks ]
	return networks

    def scan_networks(self):
        """
        Scans for wireless networks
        """
        cmd = "wpa_cli scan"
        exit_code, out, err = self._run_cmd(cmd)

        if exit_code == 0 and out == "OK":
            return True

        return False

    def select_network(self, network):
        if 'number' in network:
            cmd = "wpa_cli select_network {}".format(network.get('number'))
            exit_code, out, err = self._run_cmd(cmd)

            if exit_code == 0:
                return True

        return False

    def enable_network(self, network):
        if 'number' in network:
            cmd = "wpa_cli enable_network {}".format(network.get('number'))
            exit_code, out, err = self._run_cmd(cmd)

            if exit_code == 0:
                return True

        return False

    def disable_network(self, network):
        if 'number' in network:
            cmd = "wpa_cli disable_network {}".format(network.get('number'))
            exit_code, out, err = self._run_cmd(cmd)

            if exit_code == 0:
                return True

        return False



def get_configured_networks_from_file(file):
    """
    Returns a list of networks defined in wpa_supplicant.conf, sorted by priority
    """
    networks = []
    number = 0

    results = WpaSupplicantParser().parse((open(file).read())).asList()

    for entry in results:
        if entry[0] == "network":
            networks.append({})
            properties = entry[1]

            for prop in properties:
                networks[-1].update({prop[0]: prop[1]})

            networks[-1].update({'number': number})
            number += 1

    return sorted(networks, key=lambda k: k.get('priority', 0), reverse=True)

def get_configured_networks():
    """
    Get a list of networks reported by wpa_cli, sorted by priority
    """
    networks = WpaCli().get_configured_networks()
    return sorted(networks, key=lambda k: k.get('priority', 0), reverse=True)

def get_available_networks():
    """
    Get a list of available / discovered wireless networks
    """
    return WpaCli().get_available_networks()

def get_current_network():
    """
    Gets the currently associated network
    """
    current_network = WpaCli().get_current_network()

    for network in get_configured_networks():
        if network.get('ssid') == current_network.get('ssid'):
            current_network.update(network)

    return current_network

def scan_networks():
    """
    Scans for available wireless networks
    """
    return WpaCli().scan_networks()

def select_network(network):
    """
    Forces a network to be joined
    """
    return WpaCli().select_network(network)

def enable_network(network):
    """
    Ensures that the network is enabled (for roaming purposes) since
    forcefully selecting a network disables all others
    """
    return WpaCli().enable_network(network)

def disable_network(network):
    """
    Disable a network so it can't be joined
    """
    return WpaCli().disable_network(network)

