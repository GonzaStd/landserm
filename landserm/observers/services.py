from landserm.config.system import getServicesStartData, getServiceDetails
from landserm.config.validators import isService
from landserm.core.events import Event
from landserm.daemon.listeners import unescape_unit_filename
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
initialStates = checkStatus(servicesConfig) # Events with systemdInfo from both interfaces
for event in initialStates:
    lastState[event.subject] = event.systemdInfo
print("INITIAL STATES", lastState)
policiesIndex, _ = policiesIndexation()
process(initialStates, policiesIndex)
def handleDbus(msg):
    # msg has properties like path, interface, member, body, etc.
    path = msg.path
    if not path.startswith("/org/freedesktop/systemd1/unit/"):
        return
    
    escaped_unit_name = path.split("/")[-1]
    unit_filename = unescape_unit_filename(escaped_unit_name)
    unit_name = unit_filename[:-8]

    if len(msg.body) >= 2:
        changed = dict(msg.body[1])
        friendlyProperties = ["active", "substate", "load", "result", "exec_main", "pid"]
        dbusProperties = {
            "active": "ActiveState",
            "substate": "SubState",
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
        systemdInfo = {**lastStatePayload, **partialPayload} # Merged payload
        
        if lastStatePayload == systemdInfo: # Only work if some property has changed
            return
        
        # Only trigger event if significant properties changed (not just pid or exec_main)
        significant_props = ['active', 'substate', 'load', 'result']
        significant_changed = any(
            lastStatePayload.get(prop) != systemdInfo.get(prop) 
            for prop in significant_props
        )
        
        if not significant_changed:
            # Update lastState but don't trigger event
            lastState[unit_name] = systemdInfo
            return
        
        lastState[unit_name] = systemdInfo 
        event = Event(domain="services", kind="status", subject=unit_name, systemdInfo=systemdInfo)
        policiesIndex, _ = policiesIndexation()
        process([event], policiesIndex)

def handleJournal(entry):
    print("handle journal entry:", entry)
    for k, v in entry.items():
        print(f"{k}: {v}")
    print("New event in journal:", entry.get('MESSAGE', ''), entry.get('_SYSTEMD_UNIT', ''))