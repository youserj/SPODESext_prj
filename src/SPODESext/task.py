from dataclasses import dataclass
from DLMS_SPODES.pardata import ParValues
from StructResult import result
from DLMS_SPODES_client.client import Client
from DLMS_SPODES_client import task
from . import parameters as spodes_par


@dataclass
class SetSerialNumber(task.OK):
    data: str
    msg = "Запись серийного номера"

    async def exchange(self, c: Client) -> result.Ok | result.Error:
        return await task.WriteParValue(
            ParValues(
                par=spodes_par.SERIAL_NUMBER.VALUE,
                data=self.data,
            )
        ).exchange(c)


@dataclass
class CloseSeal(task.OK):
    msg: str = "Обжатие пломбы"

    async def exchange(self, c: Client) -> result.Ok | result.Error:
        if isinstance((res := await task.WriteParValue(
            ParValues(spodes_par.CLOSE_ELECTRIC_SEAL.VALUE, "0"),
            msg="Запись пломбы").exchange(c)
        ), result.Error):
            return res
        return result.OK
