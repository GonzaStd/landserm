import os
from landserm.config.system import getServices, getPartuuid

def isPartuuid(value: str):
    result = getPartuuid()

    lines = result.splitlines()
    partuuids = [l for l in lines if l.strip()]
    if (value in partuuids):
        return True
    else:

        return False

def isPath(value: str):
    if (os.path.exists(value)):
        return True

def isService(value: str):
    if (not value.endswith(".service")):
        value = value + ".service"

    result = getServices()

    services = []

    for line in result.splitlines():
        if not line.strip() or line.startswith("UNIT"):
            continue
        unit_name = line.split()[0]

        if unit_name.endswith(".service"):
            services.append(unit_name)

    if (value in services):
        return True
    else:
        return False