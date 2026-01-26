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

def getServiceStatus(service):
    return subprocess.run(["systemctl", "is-active", service],
            capture_output=True,
            text=True).stdout.strip() # Use string, not exit code. Without \n.


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
