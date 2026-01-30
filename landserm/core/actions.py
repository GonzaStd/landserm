import subprocess
from landserm.config.loader import landsermRoot
from landserm.config.validators import isPath
from landserm.core.delivery import deliveryLog, deliveryOLED
from landserm.core.context import expand
from landserm.core.events import Event

scriptsPath = landsermRoot + "/config/scripts/"
allowedVarsSet = {"domain", "kind", "subject", "payload"}



def execScript(eventData: Event, actionData: dict):
    scriptName = str(actionData.get("name"))
    if not scriptName.endswith(".sh"):
        scriptName += ".sh"

    scriptPath = scriptsPath + scriptName
    if not isPath(scriptPath):
        print("LOG: Invalid path or script", scriptName, "does not exist.")
        return 1
    
    arguments = list(actionData.get("args")) if "args" in actionData else False

    validArguments = list()
    for arg in actionData.get("args", []):
        expanded = expand(str(arg), eventData)
        validArguments.append(expanded)
   
    command = [scriptPath] + validArguments
    subprocess.run(command, shell=False)

supportedActions = {
     "script": execScript,
     "log": deliveryLog,
     "oled": deliveryOLED
}
def executeActions(eventData: Event, allActions: dict):
        for action in allActions:
            actionData = allActions[action]
            print("LOG: executing action", action)
            supportedActions[action](eventData, actionData)