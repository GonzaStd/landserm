import subprocess

def getPartuuid():
    return subprocess.run(
        ["lsblk", "-n", "-o", "PARTUUID"],
        capture_output=True,
        text=True,
        check=True).stdout

def getPartitions():
    return subprocess.run(["lsblk", "-o", "NAME,SIZE,PARTUUID,MOUNTPOINTS"],
            capture_output=True,
            text=True,
            check=True).stdout
    
def getServices():
    return  subprocess.run(["systemctl", "list-unit-files"],
            capture_output=True,
            text=True,
            check=True).stdout