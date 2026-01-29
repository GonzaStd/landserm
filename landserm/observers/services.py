from landserm.config.system import getServicesStartData, getServiceDetails
from landserm.config.validators import isService
from landserm.core.events import Event
from landserm.bus.systemd import unescape_unit_filename
from landserm.core.policy_engine import process, policiesIndexation
from landserm.config.loader import loadConfig, domainsConfigPaths

def checkAutoStart(servicesConfig):
    servicesData = getServicesStartData()
    targetServices = list(servicesConfig["include"])
    targetAutoStarts = dict.fromkeys(targetServices)
    events = list()
    for line in servicesData.splitlines():
        if not line.strip() or line.startswith("UNIT"):
            continue
        unitName = line.split()[0]
        if unitName in targetServices:
            state = line.split()[1]
            targetAutoStarts[unitName] = state
            targetServices.remove(unitName)
            event = Event("services", "auto_start", unitName, state)
            events.append(event)
    for missing in targetServices:
        event = Event("services", "auto_start", missing, "missing")
        events.append(event)
    
    return events

def checkStatus(servicesConfig):
    targetServices = list(servicesConfig["include"])
    events = list()
    for tService in targetServices:
        if isService(tService):
            payload = getServiceDetails(tService)
            event = Event("services", "status", tService, payload)
            events.append(event)
    return events

servicesConfig = loadConfig("services", domainsConfigPaths)
lastState = dict().fromkeys(servicesConfig.get("include"))
initialStates = checkStatus(servicesConfig) # Events with payload from both interfaces
for event in initialStates:
    lastState[event.subject] = event.payload
print("INITIAL STATES", lastState)

def handle_systemd_signal(msg):
    # msg has properties like path, interface, member, body, etc.
    path = msg.path
    if not path.startswith("/org/freedesktop/systemd1/unit/"):
        return
    
    escaped_unit_name = path.split("/")[-1]
    unit_filename = unescape_unit_filename(escaped_unit_name)
    unit_name = unit_filename[:-8]

    if len(msg.body) >= 2:
        interface = str(msg.body[0])
        changed = dict(msg.body[1])
        friendlyProperties = ["active", "sub", "load", "result", "exec_main", "pid"]
        dbusProperties = {
            "active": "ActiveState",
            "sub": "SubState",
            "load": "LoadState",
            "result": "Result",
            "exec_main": "ExecMainStatus",
            "pid": "MainPID"
        }
        
        partialPayload = dict()
        for fProperty in friendlyProperties:
            dProperty = dbusProperties[fProperty]
            if dProperty in changed:
                partialPayload[fProperty] = changed[dProperty].value

        lastStatePayload = lastState.get(unit_name, dict())
        payload = {**lastStatePayload, **partialPayload} # Merged payload
        
        if lastStatePayload == payload: # Only work if some property has changed
            return
        
        # Only trigger event if significant properties changed (not just pid or exec_main)
        significant_props = ['active', 'sub', 'load', 'result']
        significant_changed = any(
            lastStatePayload.get(prop) != payload.get(prop) 
            for prop in significant_props
        )
        
        if not significant_changed:
            # Update lastState but don't trigger event
            lastState[unit_name] = payload
            return
        
        lastState[unit_name] = payload 
        print("MESSAGE PAYLOAD", payload)

        event = Event(domain="services", kind="status", subject=unit_name, payload=payload)
        policiesIndex, _ = policiesIndexation()
        process([event], policiesIndex)

