from kp.avreceiver import AVReceiver
from kp.configuration import KPConfiguration
from kp.jrpc.jrpcserver import JRPCServer
from kp.jrpc.register import register_overloaders
from kp.log import config_logger
from kp.server import KodiProxyServer
from typing import Any, Optional


def setup_and_start(conf_path: str, event: Optional[Any] = None):
    """Sets up the server using the configuration file found at conf_path, and optionally returns the server through the threading.Event event"""
    conf = KPConfiguration(conf_path)

    config_logger(conf.logging)
    receiver = AVReceiver(conf.receiver)
    jrpc_server = JRPCServer(conf.jrpc)
    register_overloaders(jrpc_server, receiver)
    server = KodiProxyServer(conf.server, jrpc_server)

    if event:
        event.server = server
        event.set()
    server.serve()
