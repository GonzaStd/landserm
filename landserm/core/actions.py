import subprocess
from landserm.config.loader import landsermRoot
from landserm.config.validators import isPath
from landserm.config.schemas.policies import ThenBase, ScriptAction
from landserm.core.delivery import deliveryLog, deliveryOLED, deliveryPush
from landserm.core.context import expand
from landserm.core.events import Event

scriptsPath = landsermRoot + "/config/scripts/"
allowedVarsSet = {"domain", "kind", "subject", "systemdInfo", "payload"}



def execScript(eventData: Event, scriptData: ScriptAction):
    scriptName = str(scriptData.name)
    if not scriptName.endswith(".sh"):
        scriptName += ".sh"

    scriptPath = scriptsPath + scriptName
    if not isPath(scriptPath):
        print("LOG: Invalid path or script", scriptName, "does not exist.")
        return 1
    
    validArguments = list()
    for arg in scriptData.args:
        expanded = expand(str(arg), eventData)
        validArguments.append(expanded)
   
    command = [scriptPath] + validArguments
    subprocess.run(command, shell=False)

supportedActions = {
     "script": execScript,
     "log": deliveryLog,
     "oled": deliveryOLED,
     "push": deliveryPush
}
def executeActions(eventData: Event, policyActions: ThenBase):
    actionsDict = policyActions.model_dump(exclude_none=True)

    for actionName, actionData in actionsDict.items():
        if actionName not in supportedActions:
                print(f"WARNING: Unknown action '{actionName}'. Skipping.")
                continue
        print("LOG: executing action", actionName)
        supportedActions[actionName](eventData, actionData)