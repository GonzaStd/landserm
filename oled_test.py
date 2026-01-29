from luma.core.interface.serial import i2c
from luma.oled.device import sh1106  # ← Cambiar aquí
from luma.core.render import canvas
import time

serial = i2c(port=1, address=0x3C)
device = sh1106(serial, width=128, height=64)  # ← sh1106 en vez de ssd1306

device.clear()
time.sleep(0.5)

with canvas(device) as draw:
    draw.rectangle(device.bounding_box, outline="white", fill="black")
    draw.text((10, 10), "TEST", fill="white")

time.sleep(5)
device.clear()