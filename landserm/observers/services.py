from landserm.config.system import getServicesStartData, getServiceStatus
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
    targetsStatus = dict.fromkeys(targetServices)
    events = list()
    for tService in targetServices:
        if isService(tService):
            status = getServiceStatus(tService)
            targetsStatus[tService] = status
            event = Event("services", "status", tService, status)
            events.append(event)
    return events

servicesConfig = loadConfig("services", domainsConfigPaths)
lastState = dict().fromkeys(servicesConfig.get("include"))
initialStates = checkStatus(servicesConfig) # I need a function that throws events with payloads with more data. I'll implement "getServiceDetails"
for event in initialStates:
    lastState[event.subject] = event.payload

def handle_systemd_signal(msg):
    # msg has properties like path, interface, member, body, etc.
    payload=dict()
    path = msg.path
    if not path.startswith("/org/freedesktop/systemd1/unit/"):
        return
    
    escaped_unit_name = path.split("/")[-1]
    unit_filename = unescape_unit_filename(escaped_unit_name)
    unit_name = unit_filename[:-8]

    if len(msg.body) >= 2:
        interface = msg.body[0]
        changed = dict(msg.body[1])
        if interface == 'org.freedesktop.systemd1.Unit':
            friendlyData = ["active", "sub", "load", "result", "exec_main", "pid"]
            dbusData = {
                "active": "ActiveState",
                "sub": "SubState",
                "load": "LoadState",
                "result": "Result",
                "exec_main": "ExecMainStatus",
                "pid": "MainPID"
            }
            payload.fromkeys(friendlyData)
            for fd in friendlyData:
                if dbusData[fd] in changed:
                    payload[fd] = changed.get(dbusData[fd]).value
            unitLastState = lastState.get(unit_name)
            if payload == unitLastState:
                return
            unitLastState[unit_name] = payload
            event = Event(domain="services", kind="status", subject=unit_name, payload=payload)

            policiesIndex, _ = policiesIndexation()
            process([event], policiesIndex)

