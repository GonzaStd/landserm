from landserm.config.system import getServicesStartData, getServiceStatus
from landserm.config.validators import isService
from landserm.core.events import Event
from landserm.bus.systemd import unescape_unit_name
from landserm.core.policy_engine import process, policiesIndexation

def handle_systemd_signal(msg):
    # msg has properties like path, interface, member, body, etc.
    path = msg.path
    if not path.startswith("/org/freedesktop/systemd1/unit/"):
        return
    
    escaped_unit_name = path.split("/")[-1]
    unit_name = unescape_unit_name(escaped_unit_name)
    if len(msg.body) >= 2:
        interface = msg.body[0]
        changed = dict(msg.body[1])
        if interface == 'org.freedesktop.systemd1.Unit':
            state = changed.get("ActiveState").value # active/inactive/failed
            event = Event("services", "status", unit_name, state)

            policiesIndex, _ = policiesIndexation()
            process([event], policiesIndex)
    

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

