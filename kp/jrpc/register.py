from kp.jrpc.jrpcserver import JRPCServer
from kp.jrpc.volumeoverloaders import GetPropertiesOverloader, SetMuteOverloader, SetVolumeOverloader
from kp.jrpc.poweroverloaders import ApplicationQuitOverloader, SystemPropertiesOverloader


def register_overloaders(jrpc_server: JRPCServer, receiver) -> None:
    """Registers all the JRPC overloaders in the jrpc server"""
    jrpc_server.register_overloader(
        'Application.GetProperties', lambda server: GetPropertiesOverloader(server, receiver))
    jrpc_server.register_overloader(
        'Application.SetMute', lambda server: SetMuteOverloader(receiver))
    jrpc_server.register_overloader(
        'Application.SetVolume', lambda server: SetVolumeOverloader(receiver))
    jrpc_server.register_overloader(
        'Application.Quit', lambda server: ApplicationQuitOverloader(receiver))
    jrpc_server.register_overloader(
        'System.Hibernate', lambda server: ApplicationQuitOverloader(receiver))
    jrpc_server.register_overloader(
        'System.Shutdown', lambda server: ApplicationQuitOverloader(receiver))
    jrpc_server.register_overloader(
        'System.Suspend', lambda server: ApplicationQuitOverloader(receiver))
    jrpc_server.register_overloader(
        'System.GetProperties', lambda server: SystemPropertiesOverloader())
