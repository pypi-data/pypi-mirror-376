from ekfsm.devices.generic import Device
from ekfsm.devices.io4edge import IO4Edge
from io4edge_client.pixelDisplay import Client
from PIL import Image


class PixelDisplay(Device):
    """
    Device class for handling a pixel display.
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

    def describe(self) -> dict:
        """
        Returns a description of the pixel display.
        """
        describe = self.client.describe()
        desc = {
            "height": describe.height_pixel,
            "width": describe.width_pixel,
            "max_num_of_pixel": describe.max_num_of_pixel,
        }
        return desc

    @property
    def height(self) -> int:
        """
        Returns the height of the pixel display in pixels.
        """
        return self.describe()["height"]

    @property
    def width(self) -> int:
        """
        Returns the width of the pixel display in pixels.
        """
        return self.describe()["width"]

    def off(self) -> None:
        """
        Turn off the pixel display.
        @raises RuntimeError: if the command fails
        @raises TimeoutError: if the command times out
        """
        self.client.set_display_off()

    def display_image(self, path: str) -> None:
        """
        Display an image on the pixel display.
        @raises RuntimeError: if the command fails
        @raises TimeoutError: if the command times out
        """
        with Image.open(path) as img:
            img = img.convert("RGB")
            pix = img.load()

        for i in range(0, 320, 16):
            pix_area = []
            for k in range(0, 16):
                for j in range(0, 240):
                    pix_area.append(pix[j, i + k])
            self.client.set_pixel_area(0, i, 239, pix_area)

    def __repr__(self):
        return f"{self.name}; Service Address: {self.service_addr}"
