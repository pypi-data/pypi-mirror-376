from ekfsm.devices.generic import Device
from ekfsm.devices.io4edge import IO4Edge
from io4edge_client.watchdog import Client


class Watchdog(Device):
    """
    Device class for handling a color LED.
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

    def describe(self):
        pass

    def kick(self) -> None:
        """
        Kick the watchdog.
        @raises RuntimeError: if the command fails
        @raises TimeoutError: if the command times out
        """
        self.client.kick()
