from kp.jrpc.jrpcserver import JRPCServer
from kp.jrpc.volumeoverloaders import *


def register_overloaders(jrpc_server: JRPCServer, receiver) -> None:
    """Registers all the JRPC overloaders in the jrpc server"""
    jrpc_server.register_overloader(
        'Application.SetVolume', lambda server: SetVolumeOverloader(receiver))
    jrpc_server.register_overloader(
        'Application.SetMute', lambda server: SetMuteOverloader(receiver))
    jrpc_server.register_overloader(
        'Application.GetProperties', lambda server: GetPropertiesOverloader(server, receiver))
