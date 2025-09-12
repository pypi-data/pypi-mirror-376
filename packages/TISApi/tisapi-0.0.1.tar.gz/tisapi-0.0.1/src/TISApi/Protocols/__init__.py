from asyncio import get_event_loop, AbstractEventLoop
import socket
from TISApi.Protocols.udp.PacketProtocol import PacketProtocol
from homeassistant.core import HomeAssistant

loop = get_event_loop()


async def setup_udp_protocol(
    sock: socket,
    loop: AbstractEventLoop,
    udp_ip: str,
    udp_port: int,
    hass: HomeAssistant,
) -> tuple[socket.socket, PacketProtocol]:
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: PacketProtocol(sock, udp_ip, udp_port, hass),
        remote_addr=(udp_ip, udp_port),
        local_addr=("0.0.0.0", udp_port),
        allow_broadcast=True,
        reuse_port=True,
    )
    return transport, protocol
