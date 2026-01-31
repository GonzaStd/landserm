import json
import threading, time
from queue import Queue
from datetime import datetime, timezone
from landserm.config.loader import landsermRoot
from landserm.config.loader import loadConfig, resolveFilesPath
from landserm.core.context import expand
from landserm.core.events import Event

oledQueue = Queue()
oledWorker = None
oledDevice = None

def deliveryLog(eventData: Event, actionData: dict):
    if not actionData.get("enabled"):
        return 0
    
    logPath = actionData.get("path", f"{landsermRoot}/logs/landserm-{eventData.domain}.log")

    if isinstance(eventData.systemdInfo, dict):
        systemdInfo = json.dumps(eventData.systemdInfo, indent=2)
    else:
        systemdInfo = str(eventData.systemdInfo)
    
    timestamp = datetime.now().strftime("%B %d, %y %H:%M:%S")

    logMessage = f"""
[{timestamp}] {eventData.domain.upper()} EVENT
  Kind:  {eventData.kind}
  Subject:  {eventData.subject}
  systemdInfo:
  {systemdInfo}
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

def deliveryOLED(eventData: Event, actionData: dict):
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



class Push():
    def __init__(self, eventData: Event, actionData: dict, nameMethod: str):
        
        self.deliveryConfig = resolveFilesPath(base=f"{landsermRoot}/config", fileNames=["delivery"])
        self.config = loadConfig(name="delivery", configPaths=self.deliveryConfig).get("push").get(nameMethod)
        
        self.name = nameMethod

        self.eventData = eventData
        self.domain = eventData.domain
        self.subject = eventData.subject
        self.kind = eventData.kind
        self.systemdInfo = eventData.systemdInfo

        self.actionData = actionData
        self.priority = actionData.get("priority", "default")

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
            message += f"{self.eventData.systemdInfo}"
        
        self.fields = []
        if self.name == "webhook":
            if isinstance(self.systemdInfo, dict):
                for key, value in self.systemdInfo.items():
                    self.fields.append({"name": key.capitalize(), "value": str(value), "inline": True})
            else:
                self.fields.append({"name": "systemdInfo", "value": str(value), "inline": False})
            


def deliveryPush(eventData: Event, actionData: dict):
    nameMethods = ["ntfy", "gotify", "webhook"]
    selectedMethods = actionData.get("methods")

    functionMethods = {
        "ntfy": Notify,
        "gotify": Gotify,
        "webhook": Webhook
        }
    
    for method in selectedMethods:
            if not method in nameMethods:
                print(f"WARNING: Bad policy configuration, method {method} doesn't exist. Skipping method.")
                continue
            methodInstance = Push(eventData, actionData, method)
            if methodInstance.deliveryConfig.get("enabled", False):
                print(f"LOG: Policy calls the next push methods: {selectedMethods} but push is disabled in config/delivery.yaml")
                return 1
            functionMethods[method](methodInstance)

def Notify(ctx: Push):

    configNotify = ctx.config
    server = configNotify.get("server", False)
    topic = configNotify.get("topic", f"landserm-{ctx.domain}")
    auth = configNotify.get("auth", None)
    
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

    if auth:
        headers["Authorization"] = f"Bearer {auth}"
    
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
    server = ctx.config.get("server")
    token = ctx.config.get("token")

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

def Webhook(ctx: Push):
    url = ctx.config.get("url")
    headers = ctx.config.get("headers", {})

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
    if headers:
        requestHeaders.update({key: value for key, value in headers.items()})
    
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