# === sendOrderMsg_Ota ===
from abc import ABC
import logging

from pymammotion.mammotion.commands.abstract_message import AbstractMessage
from pymammotion.proto import GetInfoReq, InfoType, LubaMsg, MctlOta, MsgAttr, MsgCmdType, MsgDevice

_LOGGER = logging.getLogger(__name__)


class MessageOta(AbstractMessage, ABC):
    """Message OTA class."""

    def send_order_msg_ota(self, ota):
        luba_msg = LubaMsg(
            msgtype=MsgCmdType.EMBED_OTA,
            sender=MsgDevice.DEV_MOBILEAPP,
            rcver=self.get_msg_device(MsgCmdType.EMBED_OTA, MsgDevice.DEV_MAINCTL),
            msgattr=MsgAttr.REQ,
            seqs=self.seqs.increment_and_get() & 255,
            version=1,
            subtype=self.user_account,
            ota=ota,
        )

        return luba_msg.SerializeToString()

    def get_device_ota_info(self, log_type: int):
        todev_get_info_req = MctlOta(todev_get_info_req=GetInfoReq(type=InfoType.IT_OTA))

        _LOGGER.debug("===Send command to get upgrade details===logType:" + str(log_type))
        return self.send_order_msg_ota(todev_get_info_req)

    def get_device_info_new(self) -> bytes:
        """New device call for OTA upgrade information."""
        todev_get_info_req = MctlOta(todev_get_info_req=GetInfoReq(type=InfoType.IT_BASE))
        _LOGGER.debug("Send to get OTA upgrade information", "Get device information")
        return self.send_order_msg_ota(todev_get_info_req)
