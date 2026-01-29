import json
from datetime import datetime
from landserm.config.loader import landsermRoot

def deliveryLog(eventData: object, actionData: dict):
    if not actionData.get("enabled"):
        return 0
    
    logPath = actionData.get("path", f"{landsermRoot}/logs/landserm-{eventData.domain}.log")

    if isinstance(eventData.payload, dict):
        payload = json.dumps(eventData.payload, indent=2)
    else:
        payload = str(eventData.payload)
    
    timestamp = datetime.now().strftime("%B-%d-Y %H:%M:%S")

    logMessage = f"""
[{timestamp}] {eventData.domain.upper()} EVENT
  Kind:     {eventData.kind}
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