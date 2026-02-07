# This will be necessary for version 2, because new domains handling will be added.
import yaml
from pathlib import Path
from landserm.config.validators import isPath
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
        return yaml.safe_load(f) # -> configData

def saveConfig(name, configPaths, configData):
    with open(configPaths[name], "w") as f:
        yaml.safe_dump(configData, f)