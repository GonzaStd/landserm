import subprocess

def getPartuuid():
    result =    subprocess.run(
                ["lsblk", "-n", "-o", "PARTUUID"],
                capture_output=True,
                text=True,
                check=True).stdout
    
    lines = result.splitlines()
    partuuids = [l for l in lines if l.strip()]
    return partuuids


def getPartitions():
    return subprocess.run(["lsblk", "-o", "NAME,SIZE,PARTUUID,MOUNTPOINTS"],
            capture_output=True,
            text=True,
            check=True).stdout

def getServicesStartData():
    return subprocess.run(["systemctl", "list-unit-files"],
            capture_output=True,
            text=True,
            check=True).stdout

def getServiceDetails(service):
    output = subprocess.run(["systemctl", "show", service, "--property=ActiveState,SubState,LoadState,Result,ExecMainStatus,MainPID"],
            capture_output=True,
            text=True)
    payload = dict()
    friendlyData = ["active", "substate", "load", "result", "exec_main", "pid"]
    dbusProperties = {
        "active": "ActiveState",
        "substate": "SubState",
        "load": "LoadState",
        "result": "Result",
        "exec_main": "ExecMainStatus",
        "pid": "MainPID"
    }

    resultData = dict()
    for line in output.stdout.strip().split('\n'):
        if '=' in line:
            data = line.split('=', 1)
            key = data[0]
            value = data[1]
            resultData[key] = value

    for fd in friendlyData:
        rd = resultData.get(dbusProperties[fd])
        if rd.isdigit():
            rd = int(rd)
        payload[fd] = rd

    return payload


def getServices():
    servicesData = getServicesStartData()
    
    services = []

    for line in servicesData.splitlines():
        if not line.strip() or line.startswith("UNIT"):
            continue
        unitName = line.split()[0]

        if unitName.endswith(".service"):
            services.append(unitName)
    
    return services
