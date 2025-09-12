import pprint
from pathlib import Path
import threading
import time

from ekfsm.system import System

config = Path(__file__).parent / "sq3-only.yaml"
system = System(config, abort=True)

pprint.pprint(f"System slots {system.slots}")

system.print()

cpu = system["CPU"]
cpuB = system.cpu
cpuC = system[0]

assert cpu == cpuB == cpuC

cpu_slot = system.slots["SYSTEM_SLOT"]
cpu_slotB = system.slots.SYSTEM_SLOT
cpu_slotC = system.slots[0]

assert cpu_slot == cpu_slotB == cpu_slotC

cpu.print()
print(f"probing CPU: {cpu.probe()}")
print(
    f"inventory: {cpu.inventory.vendor()} {cpu.inventory.model()} {cpu.inventory.serial()}"
)

sq3 = system["info"]
i4e = sq3.bmc

fw_title, fw_name = i4e.identify_firmware()

print(f"Firmware: {fw_title} {fw_name}")

pixel = i4e.display

pixel.display_image(str(Path(__file__).parent / "sim/SQ3.png"))
# pixel.off()

button_array = i4e.buttons

up = button_array.up
down = button_array.down

up.handler = lambda: print("Up pressed")
down.handler = lambda: print("Down pressed")

stop_event = threading.Event()
button_thread = threading.Thread(target=button_array.read, args=(stop_event,))
button_thread.start()

# ... your main code ...
for i in range(30):
    print(f"Main loop {i}")
    time.sleep(1)

# To stop the thread:
stop_event.set()
button_thread.join()

# # currently only works with busy waiting (timeout=0) or single context
# with up.read() as up_stream:
#     for up_data in up_stream:
#         if up_data:
#             print("Up button pressed")
