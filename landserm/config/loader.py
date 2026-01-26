import yaml
from pathlib import Path
from landserm.config.validators import isPath
from landserm.config.schemas import delivery, network, policies, services, storage

landsermRoot = str(Path(__file__).resolve().parents[2])

def resolveFilesPath(base: str, fileNames: list):
    files = list()
    for name in fileNames:
        name = str(name)
        if not name.endswith(".yaml"):
            file = name + ".yaml"
        else:
            file = name
        files.append(file)
    filesPath = dict()
    filesPath.fromkeys(files)
    
    if not base.startswith(landsermRoot):
        base = landsermRoot + base
    if not base.endswith("/"):
        base = base + "/"

    for file in files:
        filePath = base + file
        name = file[:-5]
        if isPath(filePath):
            filesPath[name] = filePath
        else:
            print(f"WARNING: {file} is not in path: {base}")
    return filesPath
        
domains = ["network", "services", "storage"]

domainsConfigPaths = resolveFilesPath("/config/domains/", domains)
def loadConfig(name: str, configPaths: dict) -> dict:
    with open(configPaths[name]) as f:
        return yaml.safe_load(f)

def saveConfig(name, configPaths, configData):
    with open(configPaths[name], "w") as f:
        yaml.safe_dump(configData, f)

def getSchema(name):
    switch = {
        "delivery": delivery.schema,
        "network": network.schema,
        "policies": policies.schema,
        "services": services.schema,
        "storage": storage.schema
    }
    return switch.get(name) 