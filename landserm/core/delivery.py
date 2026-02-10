import json
import threading, time
from queue import Queue
from datetime import datetime, timezone
from luma.oled.device import ssd1306, sh1106, ssd1331
from typing import Union
from landserm.config.loader import landsermRoot
from landserm.config.loader import loadConfig, resolveConfigPath
from landserm.config.schemas.policies import ThenBase, OledAction, LogAction, PushMethods
from landserm.config.schemas.delivery import ConfigPush, ConfigOled
from landserm.core.context import expand
from landserm.core.events import Event

oledQueue = Queue()
oledWorker = None
oledDevice = None

def deliveryLog(eventData: Event, policyLogData: LogAction, priority: str):
    logsConfigData = loadConfig("delivery").logs

    if not logsConfigData.enabled:
        return 0

    if not policyLogData.enabled:
        return 0
    

    timestamp = datetime.now().strftime("%B %d, %y %H:%M:%S")
    logMessage = f"""
[{timestamp}] {eventData.domain.upper()} EVENT
Priority: {priority}
Kind:  {eventData.kind}
Subject:  {eventData.subject}
"""
    if eventData.systemdInfo:
        if isinstance(eventData.systemdInfo, dict):
            systemdInfo = json.dumps(eventData.systemdInfo, indent=2)
        else:
            systemdInfo = str(eventData.systemdInfo)
        logMessage = logMessage + \
        f"""
systemdInfo:
{systemdInfo}
{'='*50}
"""
        

    try:
        folderPath = logsConfigData.folder_path
        with open(folderPath + f"landserm-{eventData.domain}.log", "a") as logFile:
            logFile.write(logMessage)
        print(f"LOG: Written to {folderPath}")
    except PermissionError:
        print(f"ERROR: No permission to write to {folderPath}. Change permissions or change to an allowed path.")
        
def driverOLED(name: str) -> Union[ssd1331, sh1106, ssd1331]:
    from luma.core.error import DeviceNotFoundError
    try:
        from luma.core.interface.serial import i2c, spi
    except ImportError:
        print("ERROR: luma.oled is not installed. Install `luma.oled` and `pillow` with pip inside the .venv")
        return None
    
    oledConfig = loadConfig("delivery").oled
    
    width = oledConfig.width
    height = oledConfig.height
    port = oledConfig.port
    address = oledConfig.address

    device = None
    try:
        if name == "ssd1306":
            serial = i2c(port=port, address=address)
            device = ssd1306(serial, width=width, height=height)
        
        elif name == "sh1106":
            serial = i2c(port=port, address=address)
            device = sh1106(serial, width=width, height=height)
        
        elif name == "ssd1331":
            # SSD1331 typically uses SPI, not I2C
            spi_port = 0
            spi_device = 0
            serial = spi(port=spi_port, device=spi_device)
            device = ssd1331(serial, width=width, height=height)

        else:
            print(f"ERROR: Unknown OLED driver: {name}")
            return None
    except DeviceNotFoundError as e:
        print(f"OLED device not found, but config has enabled it. Error: {e}")
        return None

    return device

def oledWorkerThread(device: Union[ssd1331, sh1106, ssd1331], fontSize: int):
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

def deliveryOLED(eventData: Event, policyOledData: OledAction, priority: str):
    global oledWorker, oledDevice

    oledConfig = loadConfig("delivery").oled
    if not bool(oledConfig.enabled):
        return 0
    
    messageTemplate = policyOledData.message
    message = expand(messageTemplate, eventData)
    message += "\nPriority: " + priority
    if eventData.domain == "services" and eventData.kind == "status":
        message += "\nActive: " + eventData.systemdInfo.get("active")
    if oledDevice is None:
        driver = oledConfig.driver
        oledDevice = driverOLED(driver)
        if not oledDevice:
            return 1

    if oledWorker is None:
        fontSize = oledConfig.font_size
        oledWorker = threading.Thread(target=oledWorkerThread, args=(oledDevice, fontSize), daemon=True)
        oledWorker.start()

    duration = policyOledData.duration
    oledQueue.put((message, duration))
    print(f"LOG: OLED message queued")

class Push():
    def __init__(self, eventData: Event, nameMethod: str, priority: str):
        
        self.configPath = resolveConfigPath("delivery")
        self.config = loadConfig("delivery").push
        
        self.eventData = eventData
        self.domain = eventData.domain
        self.subject = eventData.subject
        self.kind = eventData.kind
        self.systemdInfo = eventData.systemdInfo

        self.name = nameMethod
        self.priority = priority

        self.domainEmoji = getData(self.domain,"emoji")
        self.domainColor = getData(self.domain,"color")

        self.priorEmoji = getData(self.priority,"emoji")
        self.priorText = getData(self.priority, "text")

        self.defaultTitle = f"{self.priorEmoji} | {self.domainEmoji} {self.domain.capitalize()}"
        self.defaultBody = f"Priority: {self.priorText}\nEvent **{self.kind.upper()}** from **\"{self.subject}\"** service\n"
        self.payloadText = ""

        if isinstance(self.eventData.systemdInfo, dict):
            for key, value in self.systemdInfo.items():
                self.payloadText += f"{key}: {value}\n"
        else:
            self.payloadText += f"{self.eventData.systemdInfo}"
        
        self.fields = []
        if self.name == "webhook":
            if isinstance(self.systemdInfo, dict):
                for key, value in self.systemdInfo.items():
                    self.fields.append({"name": key.capitalize(), "value": str(value), "inline": True})
            else:
                self.fields.append({"name": "systemdInfo", "value": str(value), "inline": False})
            


def deliveryPush(eventData: Event, pushData: PushMethods, priority: str):
    nameMethods = ["ntfy", "gotify", "webhook"]
    selectedMethods = pushData.root

    functionMethods = {
        "ntfy": Notify,
        "gotify": Gotify,
        "webhook": Webhook
        }
    
    for method in selectedMethods:
            if not method in nameMethods:
                print(f"WARNING: Bad policy configuration, method {method} doesn't exist. Skipping method.")
                continue
            methodInstance = Push(eventData, method, priority)
            if not getattr(methodInstance.config, method).enabled:
                print(f"LOG: Policy calls the next push method: {method} but it is disabled in your config delivery.yaml")
            functionMethods[method](methodInstance)

def Notify(ctx: Push):
    configNotify = ctx.config.ntfy
    if not configNotify.enabled:
        return 0
    server = configNotify.server
    topic = f"landserm-{ctx.domain}"
    
    if not server:
        print("ERROR: ntfy server not configured. Skipping notify.")
        return 1
    
    domainTags = {
        "services": "gear",
        "network": "globe_with_meridians", 
        "storage": "floppy_disk"
    }
    
    priorityTags = {
        "low": "information_source",
        "default": "warning",
        "high": "red_circle",
        "urgent": "rotating_light"
    }


    headers = {
        "X-Title": ctx.domain.capitalize(),
        "Priority": ctx.priority,
        "Tags": f"{domainTags.get(ctx.domain, 'bell')},{priorityTags.get(ctx.priority, 'warning')}",
        "Markdown": "yes"
    }
    
    message=f"{ctx.defaultBody}\n\nInformation:\n```{ctx.payloadText}```"

    try:
        import requests
        response = requests.post(f"{server}/{topic}", data=message.encode('utf-8'), headers=headers, timeout=10)
        if response.status_code == 200:
            print(f"LOG: ntfy notification sent to {topic}")
            return 0
        print(f"ERROR: ntfy failed with HTTP status code: {response.status_code}")
        return 1
    except Exception as e:
        print(f"ERROR: ntfy request failed: {e}")
        return 1
    
def Gotify(ctx: Push):
    configGotify = ctx.config.gotify
    if not configGotify.enabled:
        return 0
    server = configGotify.server
    token = configGotify.app_token

    if not server or not token:
        print("ERROR: Gotify server and/or token not configured. Skipping.")
        return 1
    
    priorityMap = {"low": 3, "default": 5, "high": 8, "urgent": 10}

    data = {
        "title": ctx.defaultTitle,
        "message": ctx.defaultBody,
        "priority": priorityMap.get(ctx.priority, 5)
    }

    try:
        import requests
        response = requests.post(f"{server}/message", json=data, params={"token": token}, timeout=10)
        if response.status_code == 200:
            print("LOG: Gotify notification sent")
            return 0
        print(f"ERROR: Gotify failed with HTTP status code {response.status_code}")
        return 1
    except Exception as e:
        print(f"ERROR: Gotify request failed: {e}")

DOMAIN_HEADERS = ["color", "emoji"]
DOMAINS = {
    "services": [4250465, "⚙️"],      # #40DB61 green
    "network": [5418066, "🌐"],       # #52A9DB blue
    "storage": [14368850, "💾"],      # #DB4052 red
    "custom": [14398272, "📢"]        # #DBB740 yellow
}

PRIORITY_HEADERS = ["emoji", "text"]
PRIORITIES = {
    "low": ["ℹ️", "Low"],
    "default": ["⚠️", "Normal"],
    "high": ["🔴", "High"],
    "urgent": ["🚨", "Urgent"]
}

def getData(name: str, property: str):
    if name in DOMAINS.keys():
        index = DOMAIN_HEADERS.index(property)
        return DOMAINS[name][index]
    
    elif name in PRIORITIES.keys():
        index = PRIORITY_HEADERS.index(property)
        return PRIORITIES[name][index]
    
def Webhook(ctx: Push):
    configWebhook = ctx.config.webhook
    url = configWebhook.url

    if not url:
        print("ERROR: Webhook URL not configured")
        return 1
    
    discordPayload = {
        "embeds": [{
            "title": ctx.defaultTitle,
            "description": ctx.defaultBody,
            "color": ctx.domainColor,
            "fields": ctx.fields,
            "author": {
                "name": "Landserm by GonzaStd",
                "url": "https://github.com/GonzaStd/landserm",
                "icon_url": "https://github.com/GonzaStd/landserm/blob/main/resources/GitHub_Invertocat_White.png?raw=true"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }]
    }

    requestHeaders = {"Content-Type": "application/json"}
    
    try:
        import requests
        response = response = requests.post(url, json=discordPayload, headers=requestHeaders, timeout=10)
        if response.status_code in [200, 204]:
            print("LOG: Webhook notification sent")
            return 0
        print(f"ERROR: Discord Webhook failed HTTP status code {response.status_code}")
        return 1
    except Exception as e:
        print(f"ERROR: Discord Webhook request failed: {e}")