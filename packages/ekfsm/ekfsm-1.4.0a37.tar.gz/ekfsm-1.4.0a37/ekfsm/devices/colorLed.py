from ekfsm.devices.generic import Device
from ekfsm.devices.ledArray import LEDArray
from io4edge_client.api.colorLED.python.colorLED.v1alpha1.colorLED_pb2 import Color


class ColorLED(Device):
    """
    Device class for handling a color LED.
    """

    def __init__(
        self,
        name: str,
        parent: LEDArray,
        children: list[Device] | None = None,
        abort: bool = False,
        channel_id: int = 0,
        *args,
        **kwargs,
    ):

        super().__init__(name, parent, children, abort, *args, **kwargs)

        self.name = name
        self.channel_id = channel_id

        self.client = parent.client

    def describe(self):
        pass

    def get(self) -> tuple[Color, bool]:
        """
        Get color LED state.
        @raises RuntimeError: if the command fails
        @raises TimeoutError: if the command times out
        """
        return self.client.get(self.channel_id)

    def set(self, color: Color, blink: bool) -> None:
        """
        Set the color of the color LED.
        @param Color: The color to set the LED to.
        @param blink: Whether to blink the LED.
        @raises RuntimeError: if the command fails
        @raises TimeoutError: if the command times out
        """
        self.client.set(self.channel_id, color, blink)

        def __repr__(self):
            return f"{self.name}; Channel ID: {self.channel_id}"
