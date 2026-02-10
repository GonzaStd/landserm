import subprocess
from os import environ as env
from landserm.config.validators import isPath
from landserm.config.schemas.policies import ThenBase, ScriptAction
from landserm.core.delivery import deliveryLog, deliveryOLED, deliveryPush
from landserm.core.context import expand
from landserm.core.events import Event

allowedVarsSet = {"domain", "kind", "subject", "systemdInfo", "payload"}

def execScript(eventData: Event, scriptData: ScriptAction, policyActions: ThenBase):
    scriptsPath = env.get("LANDSERM_SCRIPTS_PATH", "/etc/landserm/scripts/")
    scriptName = str(scriptData.name)
    if scriptName.strip("/"):
        scriptName = scriptName.strip("/")
        
    if not scriptName.endswith(".sh"):
        scriptName += ".sh"


    if scriptsPath.strip("/"):
        scriptsPath = scriptsPath.strip("/")
    scriptPath = f"/{scriptsPath}/{scriptName}"
    if not isPath(scriptPath):
        print("LOG: Invalid path or script", scriptName, "does not exist.")
        return 1
    
    validArguments = list()
    for arg in scriptData.args:
        expanded = expand(str(arg), eventData)
        validArguments.append(expanded)
   
    command = [scriptPath] + validArguments
    print(f"=== EXECUTING {scriptName} ===")
    subprocess.run(command, shell=False)
    print(f"=== SCRIPT ENDED ===")

supportedActions = {
     "script": execScript,
     "log": deliveryLog,
     "oled": deliveryOLED,
     "push": deliveryPush
}
def executeActions(eventData: Event, policyActions: ThenBase):
    priority = policyActions.priority
    for actionName in type(policyActions).model_fields:
        if actionName == "priority":
            continue
        
        actionData = getattr(policyActions, actionName)
        
        if actionData is None:
            continue
        
        if actionName not in supportedActions:
            print(f"WARNING: Unknown action '{actionName}'. Skipping.")
            continue
        
        print(f"LOG: executing action {actionName}")
        supportedActions[actionName](eventData, actionData, priority)