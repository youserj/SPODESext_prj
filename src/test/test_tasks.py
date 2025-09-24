import asyncio
import itertools
import time
import unittest
from DLMS_SPODES.pardata import ParValues, Parameter
from DLMS_SPODES.types import cdt
from DLMS_SPODES.cosem_interface_classes import collection
from DLMSAdapter.xml_ import xml50
from DLMSCommunicationProfile.HDLC.hdlc import HDLCParameters, HDLC
from StructResult import result, formatter
from DLMS_SPODES_communications import Network, Serial, RS485, BLEKPZ
from DLMS_SPODES_client.client import Client, IDFactory, logL
from DLMS_SPODES_client.session import DistributedTask, Session
from DLMS_SPODES_client import session
from DLMS_SPODES_client import task
from src.SPODESext import task as spodes_task

task.get_adapter(adapter := xml50)


port1 = "COM6"
port2 = "COM5"
# mac = "A0:6C:65:53:7D:86"
mac = "5C:53:10:5A:E2:4B"

id_ = collection.ID(
    man=b'XXX',
    f_id=collection.ParameterValue(b'1234567', cdt.OctetString(bytearray(b'M2M-1')).encoding),
    f_ver=collection.ParameterValue(b'1234560', cdt.OctetString(bytearray(b'1.7.15')).encoding)
)


class TestType(unittest.TestCase):
    def setUp(self) -> None:
        self.c_Serial_HIGH = Client(
            id_="c_Serial_HIGH",
            secret="30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30",  # for KPZ
            SAP=0x30,
            m_id=2,
            com_profile=HDLC(HDLCParameters(inactivity_time_out=30)),
            media=Serial(
                port=port1))
        """Serial HIGH"""

    def start_coro(self, sess: Session[result.Result]) -> None:
        async def coro(sess: Session[result.Result]) -> None:
            await sess.run()

        asyncio.run(coro(sess))

    def test_Session(self) -> None:
        self.start_coro(sess := Session(
            c=self.c_Serial_HIGH,
            tsk=task.Sequence(
                spodes_task.ChangeDisconnectControlState(1),
                spodes_task.SetSerialNumber("1234567890"),
                spodes_task.CloseSeal()
            )
        ))
        while not sess.complete:
            time.sleep(1)
        print(sess)