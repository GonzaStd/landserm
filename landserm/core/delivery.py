from landserm.config.loader import landsermRoot
def deliveryLog(eventData: object, actionData: dict):
    if not actionData.get("enabled"):
        return 0
    logPath = actionData.get("path", f"{landsermRoot}/logs/landserm-{eventData.domain}.log")
    logMessage = f"\n---START---{eventData.kind} from {eventData.subject}:\n{eventData.payload}\n---END---"
    with open(logPath, "a") as logFile:
        logFile.write(logMessage)