from typing import Callable
from ekfsm.devices.generic import Device


class Button(Device):
    """
    Device class for handling a button array.
    """

    def __init__(
        self,
        name: str,
        parent: Device,
        children: list[Device] | None = None,
        abort: bool = False,
        channel_id: int = 0,
        *args,
        **kwargs,
    ):

        super().__init__(name, parent, children, abort, *args, **kwargs)

        self.channel_id = channel_id

        self._handler: Callable | None = None

    @property
    def handler(self):
        """
        Handle button events with a callback function.
        """
        return self._handler

    @handler.setter
    def handler(self, func: Callable | None, *args, **kwargs):
        """
        Handle button events with a callback function.
        """
        if callable(func):
            self._handler = func
        else:
            self._handler = None

    def __repr__(self):
        return f"{self.name}; Channel ID: {self.channel_id}"
