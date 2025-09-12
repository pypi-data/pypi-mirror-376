import pprint
import logging
from pathlib import Path

from ekfsm.system import System
from ekfsm.devices.colorLed import Color

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

config = Path(__file__).parent / "cctv.yaml"
system = System(config, abort=True)

pprint.pprint(f"System slots {system.slots}")

system.print()

cpu = system["CPU"]
cpuB = system.cpu
cpuC = system[0]

assert cpu == cpuB == cpuC

# To check why below is failing
# cpu_slot = system.slots["SYSTEM_SLOT"]
# cpu_slotB = system.slots.SYSTEM_SLOT
# cpu_slotC = system.slots[0]

# assert cpu_slot == cpu_slotB == cpu_slotC

cpu.print()
print(f"probing CPU: {cpu.probe()}")
print(
    f"inventory: {cpu.inventory.vendor()} {cpu.inventory.model()} {cpu.inventory.serial()}"
)

smc = system.smc

smc.print()
smc.leds.led0.set(Color.RED, True)
