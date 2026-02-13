import subprocess
from os import environ as env
from landserm.config.validators import isPath
from landserm.config.schemas.policies import ThenBase, ScriptAction
from landserm.core.delivery import deliveryLog, deliveryOLED, deliveryPush
from landserm.core.context import expand
from landserm.core.events import Event
from landserm.core.logger import getLogger

logger = getLogger(context="actions")

allowedVarsSet = {"domain", "kind", "subject", "systemdInfo", "payload"}

def execScript(eventData: Event, scriptData: ScriptAction, priority: str):
    scriptsPath = env.get("LANDSERM_SCRIPTS_PATH", "/opt/landserm/user/scripts/")
    scriptName = str(scriptData.name)
    if scriptName.strip("/"):
        scriptName = scriptName.strip("/")
        
    if not scriptName.endswith(".sh"):
        scriptName += ".sh"


    if scriptsPath.strip("/"):
        scriptsPath = scriptsPath.strip("/")
    scriptPath = f"/{scriptsPath}/{scriptName}"
    if not isPath(scriptPath):
        logger.warning(f"Invalid path or script '{scriptName}' does not exist.")
        return 1
    
    validArguments = list()
    for arg in scriptData.args:
        expanded = expand(str(arg), eventData)
        validArguments.append(expanded)
   
    command = [scriptPath] + validArguments
    logger.info(f"Executing {scriptName} (Priority: {priority})")
    try:
        result = subprocess.run(command, shell=False, capture_output=True, text=True)
        if result.stdout:
            logger.info(f"Output:\n{result.stdout}")
        if result.returncode != 0:
            logger.warning(f"Exit code: {result.returncode}")
            if result.stderr:
                logger.error(f"Error: {result.stderr}")
    except PermissionError as e:
        logger.error(f"Couldn't execute script: {scriptName} Error: {e}")
    logger.info(f"Script ended")

supportedActions = {
     "script": execScript,
     "log": deliveryLog,
     "oled": deliveryOLED,
     "push": deliveryPush
}
def executeActions(eventData: Event, policyActions: ThenBase):
    
        priority = policyActions.priority
        for actionName in type(policyActions).model_fields:
            try:
                if actionName == "priority":
                    continue
                
                actionData = getattr(policyActions, actionName)
                
                if actionData is None:
                    continue
                
                if actionName not in supportedActions:
                    logger.warning(f"Unknown action '{actionName}'. Skipping.")
                    continue
                
                logger.info(f"Executing action {actionName}")
                supportedActions[actionName](eventData, actionData, priority)

            except PermissionError as e:
                logger.error(f"No permission to execute the following action: {actionName} Error: {e}")