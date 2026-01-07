import subprocess
def getPartitions(): => str
    return subprocess.run(["lsblk", "-o", "NAME,SIZE,PARTUUID,MOUNTPOINTS"],
            capture_output=True,
            text=True,
            check=True).stdout
    
def getServices(): => str
    return  subprocess.run(["systemctl", "list-unit-files"],
            capture_output=True,
            text=True,
            check=True).stdout