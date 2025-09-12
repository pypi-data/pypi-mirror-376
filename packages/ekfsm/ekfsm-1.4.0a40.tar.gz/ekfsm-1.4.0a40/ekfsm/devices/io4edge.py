from typing import Callable, Optional
from ekfsm.core.components import HWModule
from ekfsm.devices.generic import Device
import io4edge_client.core.coreclient as Client

from re import sub


class IO4Edge(Device):
    """
    Device class for handling IO4Edge devices.
    """

    def __init__(
        self,
        name: str,
        parent: HWModule | None = None,
        children: list[Device] | None = None,
        abort: bool = False,
        *args,
        **kwargs,
    ):

        super().__init__(name, parent, children, abort, *args, **kwargs)

        attr = self.hw_module.slot.attributes
        if (
            attr is None
            or not hasattr(attr, "slot_coding")
            or getattr(attr, "slot_coding") is None
        ):
            raise ValueError(
                f"Slot attributes for {self.hw_module.slot.name} are not set or do not contain 'slot_coding'."
            )
        else:
            geoaddr = int(attr.slot_coding)
            self._geoaddr = geoaddr

        _, module_name = sub(r"-.*$", "", self.hw_module.board_type).split(maxsplit=1)
        self._module_name = module_name
        self.client = Client.new_core_client(self.deviceId)

    @property
    def deviceId(self) -> str:
        """
        Returns the device ID for the IO4Edge device.
        The device ID is a combination of the module name and the geo address.
        """
        return f"{self._module_name}-geo_addr{self._geoaddr:02d}"

    def identify_firmware(self) -> tuple[str, str]:
        return (
            self.client.identify_firmware().title,
            self.client.identify_firmware().version,
        )

    def load_firmware(
        self, cfg: bytes, progress_callback: Optional[Callable[[float], None]] = None
    ) -> None:
        """
        Load firmware onto the IO4Edge device.

        cfg
            Firmware configuration bytes.
        progress_callback
            Optional callback for progress updates.
        """
        self.client.load_firmware(cfg, progress_callback)

    def restart(self) -> None:
        self.client.restart()

    def load_parameter(self, name: str, value: str) -> None:
        """
        Set a parameter onto the IO4Edge device.

        cfg
            The name of the parameter to load.
        value
            The value to set for the parameter.
        """
        self.client.set_persistent_parameter(name, value)

    def get_parameter(self, name: str) -> str:
        """
        Get a parameter value from the IO4Edge device.

        Returns
            The value of the requested parameter.
        """
        return self.client.get_persistent_parameter(name)

    def __repr__(self):
        return f"{self.name}; DeviceId: {self.deviceId}"
