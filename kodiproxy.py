#!/usr/bin/python3

import argparse
from kp.main import setup_and_start

parser = argparse.ArgumentParser(
    prog='Kodi Proxy',
    description='Starts a proxy that forwards most jrpc requests to a Kodi server but overrides some of them.')
parser.add_argument('-c', '--conf', default='/usr/lib/kodiproxy/kodiproxy.json',
                    help='configuration file to override the default one')
args = parser.parse_args()
setup_and_start(args.conf)
