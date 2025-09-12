from ekfsm.devices.generic import Device
from ekfsm.devices.io4edge import IO4Edge
from io4edge_client.analogintypea import Client


class ThermalHumidity(Device):
    """
    Device class for handling a thermal humidity sensor.
    """

    def __init__(
        self,
        name: str,
        parent: IO4Edge,
        children: list[Device] | None = None,
        abort: bool = False,
        service_suffix: str | None = None,
        *args,
        **kwargs,
    ):

        super().__init__(name, parent, children, abort, *args, **kwargs)

        self.name = name

        if service_suffix is not None:
            self.service_suffix = service_suffix
        else:
            self.service_suffix = name

        self.service_addr = f"{parent.deviceId}-{self.service_suffix}"

        self.client = Client(self.service_addr)

    def __repr__(self):
        return f"{self.name}; Service Address: {self.service_addr}"

    def temperature(self) -> float:
        """
        Get the temperature in Celsius.
        @raises RuntimeError: if the command fails
        @raises TimeoutError: if the command times out
        """
        return self.client.value()
