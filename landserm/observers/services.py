from landserm.daemon.listeners import unescape_unit_filename
from landserm.config.system import getServicesStartData, getServiceDetails
from landserm.config.validators import isService
from landserm.config.loader import loadConfig
from landserm.config.schemas.domains import ServicesConfig
from landserm.core.events import Event
from landserm.core.policy_engine import process, policiesIndexation
from landserm.core.logger import getLogger
from rich.pretty import Pretty

logger = getLogger(context="services")

def checkAutoStart(servicesConfig: ServicesConfig):
    servicesData = getServicesStartData()
    targetServices = list(servicesConfig.include)
    targetAutoStarts = dict.fromkeys(targetServices)
    events = list()
    for line in servicesData.splitlines():
        if not line.strip() or line.startswith("UNIT"):
            continue
        unitName = line.split()[0]
        if unitName in targetServices:
            tService = unitName
            state = line.split()[1]
            targetAutoStarts[unitName] = state
            targetServices.remove(unitName)
            event = Event("services", "auto_start", tService, state)
            events.append(event)
    return events

def checkStatus(servicesConfig: ServicesConfig):
    targetServices = servicesConfig.include
    events = list()
    for tService in targetServices:
        if isService(tService):
            payload = getServiceDetails(tService)
            event = Event("services", "status", tService, payload)
            events.append(event)
    return events

servicesConfig = loadConfig("domains", domain="services")

lastSystemdInfo = {service: {"status":{}, "auto_start": None} for service in servicesConfig.include}
initialStates = checkStatus(servicesConfig) + checkAutoStart(servicesConfig)  # Events with systemdInfo from both interfaces
for event in initialStates:
    lastSystemdInfo[event.subject][event.kind] = event.systemdInfo

logger.info("Initial states:", Pretty(lastSystemdInfo))
policiesIndex = policiesIndexation()

def handleDbus(msg):
    # msg has properties like path, interface, member, body, etc.
    path = msg.path
    if not path.startswith("/org/freedesktop/systemd1/unit/"):
        return
    
    escaped_unit_name = path.split("/")[-1]
    unit_filename = unescape_unit_filename(escaped_unit_name)
    unit_name = unit_filename[:-8]
    if unit_name not in servicesConfig.include:
        return 0
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

        lastStatePayload = lastSystemdInfo[unit_name].get("status", dict()) # For now it only works with "status" kind.
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
            lastSystemdInfo[unit_name]["status"] = systemdInfo
            return
        
        lastSystemdInfo[unit_name]["status"] = systemdInfo 
        event = Event(domain="services", kind="status", subject=unit_name, systemdInfo=systemdInfo)
        logger.info(f"Event triggered for {unit_name}:", Pretty(systemdInfo))
        policiesIndex = policiesIndexation()
        process([event], policiesIndex)