from dataclasses import dataclass
from DLMS_SPODES.pardata import ParValues
from StructResult import result
from DLMS_SPODES.types import cdt, cst
from DLMS_SPODES.cosem_interface_classes import disconnect_control
from DLMS_SPODES.cosem_interface_classes import parameters as dlms_par
from DLMS_SPODES.types.implementations import integers
from DLMS_SPODES_client.client import Client
from DLMS_SPODES_client import task
from DLMS_SPODES import exceptions as exc
from . import parameters as spodes_par


@dataclass
class SetSerialNumber(task.OK):
    data: str
    msg = "Запись серийного номера"

    async def exchange(self, c: Client) -> result.Ok | result.Error:
        return await task.WriteParValue(
            ParValues(
                par=spodes_par.SERIAL_NUMBER.value,
                data=self.data,
            )
        ).exchange(c)


@dataclass
class CloseSeal(task.OK):
    msg: str = "Обжатие пломбы"

    async def exchange(self, c: Client) -> result.Ok | result.Error:
        if isinstance((res := await task.WriteParValue(
            ParValues(spodes_par.CLOSE_ELECTRIC_SEAL.value, "0"),
            msg="Запись пломбы").exchange(c)
        ), result.Error):
            return res
        return result.OK


@dataclass
class ChangeDisconnectControlState(task.OK):
    state: int
    b: int = 0
    msg: str = "Смена состояния DisconnectControl"

    def __post_init__(self) -> None:
        if not (0 <= self.state <= 2):
            raise ValueError(F"got wrong {self.state=}, expect 0..2")

    async def exchange(self, c: Client) -> result.Ok | result.Error:
        """return output and control state"""
        par = dlms_par.DisconnectControl.from_b(self.b)
        obj = c.objects.getDISCONNECT_CONTROL(0)
        if isinstance(res := await task.Sequence(
            task.Par2Data[disconnect_control.ControlState](par.control_state),
            task.Par2Data[disconnect_control.ControlMode](par.control_mode),
            err_ignore=False
        ).exchange(c), result.Error):
            return res
        state, mode = res.value
        transitions: str = mode.get_letters(int(obj.control_mode))
        match int(state), self.state:
            case 0, 1 if "a" in transitions:
                if isinstance(res2 := await task.Execute2(par.remote_reconnect, integers.Only0()).exchange(c), result.Error):
                    return res2
            case 0, 2 if "d" in transitions:
                if isinstance(res2 := await task.Execute2(par.remote_reconnect, integers.Only0()).exchange(c), result.Error):
                    return res2
            case 1, 0 if "b" in transitions:
                if isinstance(res2 := await task.Execute2(par.remote_disconnect, integers.Only0()).exchange(c), result.Error):
                    return res2
            case 2, 0 if "c" in transitions:
                if isinstance(res2 := await task.Execute2(par.remote_disconnect, integers.Only0()).exchange(c), result.Error):
                    return res2
            case 2, 1 if "c" in transitions and "a" in transitions:
                if isinstance(res3 := await task.Sequence(
                    task.Execute2(par.remote_disconnect, integers.Only0()),
                    task.Execute2(par.remote_reconnect, integers.Only0()),
                    err_ignore=False
                ).exchange(c), result.Error):
                    return res3
            case 1, 2 if "b" in transitions and "d" in transitions:
                if isinstance(res3 := await task.Sequence(
                    task.Execute2(par.remote_disconnect, integers.Only0()),
                    task.Execute2(par.remote_reconnect, integers.Only0()),
                    err_ignore=False
                ).exchange(c), result.Error):
                    return res3
            case a, b if a == b:
                return result.Error.from_e(exc.DLMSException("уже имеется <{disconnect_control.ControlState(self.state)}>"))
            case _:
                return result.Error.from_e(exc.DLMSException(F"переключение на <{disconnect_control.ControlState(self.state)}> невозможно из текущего <{obj.control_state}>"))
        return result.OK
