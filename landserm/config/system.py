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

def getServicesData():
    return subprocess.run(["systemctl", "list-unit-files"],
            capture_output=True,
            text=True,
            check=True).stdout

def getServices():
    services_data = getServicesData()
    
    services = []

    for line in services_data.splitlines():
        if not line.strip() or line.startswith("UNIT"):
            continue
        unit_name = line.split()[0]

        if unit_name.endswith(".service"):
            services.append(unit_name)
    
    return services
