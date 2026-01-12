from landserm.config.system import getServicesData
from landserm.core.events import Event

def scan(services_config):
    services_data = getServicesData()
    target_services = list(services_config["include"])
    target_states = dict.fromkeys(target_services)
    events = list()
    for line in services_data.splitlines():
        if not line.strip() or line.startswith("UNIT"):
            continue
        unit_name = line.split()[0]
        if unit_name in target_services:
            state = line.split()[1]
            target_states[unit_name] = state
            target_services.remove(unit_name)
            event = Event("services", "state", unit_name, state, "info")
            events.append(event)
    for missing in target_services:
        event = Event("services", "state", missing, "missing", "info")
        events.append(event)
    
    return events