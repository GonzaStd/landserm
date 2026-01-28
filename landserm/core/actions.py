import subprocess
from landserm.config.loader import landsermRoot
from landserm.config.validators import isPath
from landserm.core.delivery import deliveryLog

scriptsPath = landsermRoot + "/config/scripts/"
allowedVarsSet = {"domain", "kind", "subject", "payload"}



def execScript(eventData: object, actionData: dict):
    scriptName = str(actionData.get("name"))
    if not scriptName.endswith(".sh"):
        scriptName += ".sh"

    scriptPath = scriptsPath + scriptName
    if not isPath(scriptPath):
        print("LOG: Invalid path or script", scriptName, "does not exist.")
        return 1
    
    arguments = list(actionData.get("args")) if "args" in actionData else False
    validArguments = list()

    if arguments:
        for arg in arguments:
            arg = str(arg)
            if arg.startswith("$"):
                arg = arg[1:]
                if arg in allowedVarsSet:
                    validArguments.append(getattr(eventData, arg))
                elif '.' in arg and arg.split(".")[0] == "payload":
                    payloadData = dict(eventData.payload)
                    keys = arg.split(".")[1:]
                    pivot = payloadData
                    for key in keys:
                        pivot = pivot[key]
                    validArguments.append(str(pivot))
            else:
                validArguments.append(str(arg))
    
    command = validArguments
    command.insert(0, scriptPath)
    subprocess.run(command, shell=False)

supportedActions = {
     "script": execScript,
     "log": deliveryLog
}
def executeActions(eventData: object, allActions: dict):
        for action in allActions:
            actionData = allActions[action]
            print("LOG: executing action", action)
            supportedActions[action](eventData, actionData)