import subprocess

def isPartuuid(value: str):
    result = subprocess.run(
        ["lsblk", "-n", "-o", "PARTUUID"],
        capture_output=True,
        text=True,
        check=True
    )

    lines = result.stdout.splitlines()
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
        value.append(".service")

    result = subprocess.run(["systemctl", "list-unit-files", "|", "awk", "'$1 /\\.service$/ {print $1}'"],
    capture_output = True,
    text = True,
    check = True)

    lines = result.stdout.splitlines()
    services = [s for s in lines if s.strip()]
    if (value in services):
        return True
    else:
        return False