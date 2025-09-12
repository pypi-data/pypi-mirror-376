from homeassistant.core import HomeAssistant
import logging


class PacketDispatcher:
    def __init__(self, hass: HomeAssistant, OPERATIONS_DICT: dict):
        self.hass = hass
        self.operations_dict = OPERATIONS_DICT

    async def dispatch_packet(self, info):
        try:
            packet_handler = self.operations_dict.get(
                tuple(info["operation_code"]), "unknown operation"
            )
            if packet_handler != "unknown operation":
                await packet_handler(self.hass, info)
            else:
                logging.error(f"unknown operation code: {info['operation_code']}")
        except Exception as e:
            logging.error(f"error in dispatching packet: {e} , {info}")
