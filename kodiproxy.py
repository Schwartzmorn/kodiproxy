#!/usr/bin/python3

from kp.configuration import KPConfiguration
from kp.log import config_logger
from kp.server import KodiProxyServer

if __name__ == '__main__':
    # TODO add path
    conf = KPConfiguration()
    config_logger(conf.logging)
    server = KodiProxyServer(conf.server)
    server.serve()
