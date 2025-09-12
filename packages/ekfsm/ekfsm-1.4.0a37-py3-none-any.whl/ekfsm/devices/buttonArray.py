import threading
from ekfsm.devices.button import Button
from ekfsm.devices.generic import Device
from ekfsm.devices.io4edge import IO4Edge
import io4edge_client.binaryiotypeb as binio
import io4edge_client.functionblock as fb


class ButtonArray(Device):
    """
    Device class for handling a button array.
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

        self.client = binio.Client(self.service_addr)

        self.subscriptionType = binio.Pb.SubscriptionType.BINARYIOTYPEB_ON_RISING_EDGE
        self.stream_cfg = fb.Pb.StreamControlStart(
            bucketSamples=1,  # 1 sample per bucket, also ein event pro bucket
            keepaliveInterval=10000,  # rueckmeldung auch ohne events alle 10 Sekunden
            bufferedSamples=2,  # 2 samples werden gepuffert
            low_latency_mode=True,  # schickt soweit moeglich sofort die Events
        )

    def read(self, stop_event: threading.Event | None = None, timeout: float = 0.1):
        """
        Read all button events and dispatch to handlers.
        """
        self.client.start_stream(
            binio.Pb.StreamControlStart(
                subscribeChannel=tuple(
                    binio.Pb.SubscribeChannel(
                        channel=button.channel_id,
                        subscriptionType=self.subscriptionType,
                    )
                    for button in self.children
                    if isinstance(button, Button)
                )
            ),
            self.stream_cfg,
        )
        try:
            while not (stop_event and stop_event.is_set()):
                try:
                    _, samples = self.client.read_stream(timeout=timeout)
                    for sample in samples.samples:
                        for button in self.children:
                            if isinstance(button, Button):
                                pressed = bool(sample.inputs & (1 << button.channel_id))
                                if pressed and button.handler:
                                    button.handler()
                except TimeoutError:
                    continue
        finally:
            try:
                if stop_event:
                    stop_event.clear()
                self.client.stop_stream()
            except TimeoutError:
                pass

    def __repr__(self):
        return f"{self.name}; Service Address: {self.service_addr}"
