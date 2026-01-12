from landserm.config.system import getServicesData
from landserm.core.events import Event

def scan(servicesConfig):
    servicesData = getServicesData()
    targetServices = list(servicesConfig["include"])
    targetStates = dict.fromkeys(targetServices)
    events = list()
    for line in servicesData.splitlines():
        if not line.strip() or line.startswith("UNIT"):
            continue
        unitName = line.split()[0]
        if unitName in targetServices:
            state = line.split()[1]
            targetStates[unitName] = state
            targetServices.remove(unitName)
            event = Event("services", "state", unitName, state)
            events.append(event)
    for missing in targetServices:
        event = Event("services", "state", missing, "missing")
        events.append(event)
    
    return events