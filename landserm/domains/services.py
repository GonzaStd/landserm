from landserm.config.system import getServicesData

def scan(services_config):
    services_data = getServicesData()
    target_services = list(services_config["include"])
    target_states = dict.fromkeys(target_services)
    for line in services_data.splitlines():
        if not line.strip() or line.startswith("UNIT"):
            continue
        unit_name = line.split()[0]
        if unit_name in target_services:
            state = line.split()[1]
            target_states[unit_name] = state
            target_services.remove(unit_name)

    
    return target_states, target_services