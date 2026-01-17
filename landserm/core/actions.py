import subprocess
from landserm.config.loader import landsermRoot
from landserm.config.validators import isPath

scriptsPath = landsermRoot + "/config/scripts/"
allowedVarsSet = {"domain", "kind", "subject", "payload"}



def execScript(context: dict, scriptData: dict):
    scriptName = str(scriptData["name"])
    if not scriptName.endswith(".sh"):
        scriptName += ".sh"

    scriptPath = scriptsPath + scriptName
    if not isPath(scriptPath):
        print("LOG: Invalid path or script", scriptName, "does not exist.")
        return 1
    
    arguments = list(scriptData["args"])
    validArguments = list()

    if arguments:
        for arg in arguments:
            arg = str(arg)
            if arg.startswith("$") and arg[1:] in allowedVarsSet:
                contextVarName = arg[1:]
                if contextVarName in context.keys():
                    validArguments.append(context[contextVarName]) 
            else:
                validArguments.append(arg)
    
    command = validArguments
    command.insert(0, scriptPath)
    subprocess.run(command, shell=False)

supportedActions = {
     "script": execScript
}
def executeActions(context: dict, allActions: dict):
        for action in allActions:
            actionData = allActions[action]
            print("LOG: executing action", action)
            supportedActions[action](context, actionData)