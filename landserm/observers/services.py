from landserm.config.system import getServicesStartData, getServiceStatus
from landserm.config.validators import isService
from landserm.core.events import Event

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