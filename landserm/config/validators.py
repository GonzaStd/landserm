import os
from landserm.config.system import getServices, getPartuuid


def isPath(value: str):
    if (os.path.exists(value)):
        return True

def isPartuuid(value: str):
    partuuids = getPartuuid()
    return (value in partuuids)
    
def isService(value: str):
    if (not value.endswith(".service")):
        value = value + ".service"
    services = getServices()
    return (value in services)