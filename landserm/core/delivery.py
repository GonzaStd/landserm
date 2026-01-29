import json
import threading, time
from queue import Queue
from datetime import datetime
from landserm.config.loader import landsermRoot
from landserm.config.loader import loadConfig, resolveFilesPath
from landserm.core.context import expand

oledQueue = Queue()
oledWorker = None
oledDevice = None

def deliveryLog(eventData: object, actionData: dict):
    if not actionData.get("enabled"):
        return 0
    
    logPath = actionData.get("path", f"{landsermRoot}/logs/landserm-{eventData.domain}.log")

    if isinstance(eventData.payload, dict):
        payload = json.dumps(eventData.payload, indent=2)
    else:
        payload = str(eventData.payload)
    
    timestamp = datetime.now().strftime("%B %d, %y %H:%M:%S")

    logMessage = f"""
[{timestamp}] {eventData.domain.upper()} EVENT
  Kind:  {eventData.kind}
  Subject:  {eventData.subject}
  Payload:
  {payload}
{'='*50}
"""
    try:
        with open(logPath, "a") as logFile:
            logFile.write(logMessage)
        print(f"LOG: Written to {logPath}")
    except PermissionError:
        print(f"ERROR: No permission to write to {logPath}. Change permissions or change to an allowed path.\
               You can skip \"path\" in config and it will use the default path: {landsermRoot}/logs/landserm-{eventData.domain}.log")
        
def driverOLED(name: str, config: dict):
    from luma.core.error import DeviceNotFoundError
    try:
        from luma.core.interface.serial import i2c, spi
        from luma.core.render import canvas
        from PIL import ImageFont, ImageDraw
    except ImportError:
        print("ERROR: luma.oled is not installed. Install `luma.oled` and `pillow` with pip inside the .venv")
        return None
    
    width = config.get("width", 128)
    height = config.get("height", 64)
    port = config.get("port", 1)
    address = config.get("address", 0x3C)

    device = None
    try:
        if name == "ssd1306":
            from luma.oled.device import ssd1306
            serial = i2c(port=port, address=address)
            device = ssd1306(serial, width=width, height=height)
        
        elif name == "sh1106":
            from luma.oled.device import sh1106
            serial = i2c(port=port, address=address)
            device = sh1106(serial, width=width, height=height)
        
        elif name == "ssd1331":
            from luma.oled.device import ssd1331
            # SSD1331 typically uses SPI, not I2C
            spi_port = config.get("spi_port", 0)
            spi_device = config.get("spi_device", 0)
            serial = spi(port=spi_port, device=spi_device)
            device = ssd1331(serial, width=width, height=height)

        else:
            print(f"ERROR: Unknown OLED driver: {name}")
            return None
    except DeviceNotFoundError as e:
        print(f"OLED device not found, but config has enabled it. Error: {e}")
        return None

    return device

def oledWorkerThread(device, fontSize):
    from luma.core.render import canvas
    from PIL import ImageFont
    import re

    print("LOG: OLED worker thread started")

    try:
        fontRegular = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", fontSize)
        fontBold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fontSize)
        print(f"LOG: Fonts loaded successfully")
    except Exception as e:
        print(f"WARN: Could not load TrueType fonts: {e}")
        fontRegular = ImageFont.load_default()
        fontBold = fontRegular

    def parse_bold(line):
        segments = []
        pos = 0
        
        for match in re.finditer(r'\*\*(.+?)\*\*', line):
            # Add regular text before bold
            if match.start() > pos:
                segments.append((line[pos:match.start()], False))
            # Add bold text
            segments.append((match.group(1), True))
            pos = match.end()
        
        # Add remaining regular text
        if pos < len(line):
            segments.append((line[pos:], False))
        
        return segments if segments else [(line, False)]

    while True:
        print("LOG: OLED worker waiting for message...")
        message, duration = oledQueue.get()
        if message is None:
            break

        print(f"LOG: OLED displaying: {message}")

        try:
            with canvas(device) as draw:
                y = 0
                for line in message.split('\n'):
                    x = 0
                    segments = parse_bold(line)
                    
                    for text, is_bold in segments:
                        if text:
                            font = fontBold if is_bold else fontRegular
                            draw.text((x, y), text, font=font, fill="white")
                            bbox = draw.textbbox((x, y), text, font=font)
                            x = bbox[2]
                    
                    y += fontSize + 2

            time.sleep(duration)
            device.clear()
            print("LOG: OLED cleared")
        except Exception as e:
            print(f"ERROR: OLED failed: {e}")

        oledQueue.task_done()

def deliveryOLED(eventData: object, actionData: dict):
    global oledWorker, oledDevice

    oledConfig = loadConfig("delivery", resolveFilesPath(f"{landsermRoot}/config" , ["delivery"])).get("oled", {})

    if not oledConfig.get("enabled", False):
        return 0
    
    messageTemplate = actionData.get("message", "Subject:$subject\nKind:$kind")
    message = expand(messageTemplate, eventData)

    if oledDevice is None:
        driver = oledConfig.get("driver")
        oledDevice = driverOLED(driver, oledConfig)
        if not oledDevice:
            return 1

    if oledWorker is None:
        fontSize = oledConfig.get("font_size", 12)
        oledWorker = threading.Thread(target=oledWorkerThread, args=(oledDevice, fontSize), daemon=True)
        oledWorker.start()

    duration = actionData.get("duration", 5)
    oledQueue.put((message, duration))
    print(f"LOG: OLED message queued")
