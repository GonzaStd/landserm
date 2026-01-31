import subprocess, psutil

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
    output = subprocess.run(
        ["systemctl", "show", service, 
         "--property=ActiveState,SubState,LoadState,Result,ExecMainStatus,MainPID,MemoryCurrent,CPUUsageNSec"],
        capture_output=True,
        text=True
    )
    
    systemdInfo = {}
    
    propertyMap = {
        "ActiveState": "active",
        "SubState": "substate",
        "LoadState": "load",
        "Result": "result",
        "ExecMainStatus": "exec_main",
        "MainPID": "pid",
        "MemoryCurrent": "memory_usage_mb",
        "CPUUsageNSec": "cpu_usage_sec"
    }
    
    resultData = {}
    for line in output.stdout.strip().split('\n'):
        if '=' in line:
            key, value = line.split('=', 1)
            resultData[key] = value
    
    # Mapear a nombres amigables
    for dbusKey, friendlyKey in propertyMap.items():
        value = resultData.get(dbusKey, "")
        
        if value.isdigit():
            systemdInfo[friendlyKey] = int(value)
        else:
            systemdInfo[friendlyKey] = value
    
    if systemdInfo.get("memory_usage_mb"):
        systemdInfo["memory_usage_mb"] = round(systemdInfo["memory_usage_mb"] / (1024 * 1024) , 2)
    else:
        systemdInfo["memory_usage_mb"] = 0.0
    
    if systemdInfo.get("cpu_usage_sec"):
        systemdInfo["cpu_usage_sec"] = round(systemdInfo["cpu_usage_sec"] / 1_000_000_000, 2)
    else:
        systemdInfo["cpu_usage_sec"] = 0
    
    
    return systemdInfo


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
