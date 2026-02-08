# This will be necessary for version 2, because new domains handling will be added.
import yaml
import importlib
from dotenv import load_dotenv
from os import environ as env
from os import path as osPath
from pathlib import Path
from landserm.config.validators import isPath

env_paths = [
    Path("/etc/landserm/.env"),
    Path.home() / ".landserm" / ".env",
    Path.cwd() / ".env"
]

for env_file in env_paths:
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Loaded env from {env_file}")
        break
else:
    print("WARNING: No .env file found, using defaults")

landsermRoot = str(Path(__file__).resolve().parents[2])
defaultConfigBase = landsermRoot + "/config-template/"
chosenConfigBase = env.get("LANDSERM_CONFIG_PATH", "")

def resolveConfigPath(fileNames: list | str, configTailFolder: str = "") -> dict: 
    if osPath.isdir(chosenConfigBase):
        configBase = chosenConfigBase
    else:
        if not chosenConfigBase or chosenConfigBase == "":
            print(f"WARNING: You didn't configured a base config")
        else:
            print(f"WARNING: Your base config ({chosenConfigBase}) does not exist")
        print(f"INFO: Using {defaultConfigBase}")
        configBase = defaultConfigBase

    files = list()
    if isinstance(fileNames, str):
        fileNames = [fileNames]
    for name in fileNames:
        name = str(name)
        if not name.endswith(".yaml"):
            file = name + ".yaml"
        else:
            file = name
        files.append(file)
    
    configBase = configBase.strip("/")
    configTailFolder = configTailFolder.strip("/")
    if configTailFolder:
        configFolderPath = f"/{configBase}/{configTailFolder}/"
    else:
        configFolderPath =  f"/{configBase}/"

    filesPath = dict()
    for file in files:
        filePath = configFolderPath + file
        name = file[:-5]
        if isPath(filePath):
            filesPath[name] = filePath
        else:
            print(f"WARNING: {file} is not in path: {configFolderPath}")
    return filesPath
        
domains = ["network", "services", "storage"]

def loadConfig(configType: str, domain: str = None) -> dict:

    configModule = importlib.import_module(f"landserm.config.schemas.{configType}")

    if configType == "delivery":
        fileName = configType
        configPaths = resolveConfigPath(fileName)
        SchemaClass = getattr(configModule, "DeliveryConfig")

    if configType in ["domains", "policies"]:
        if not domain:
            raise ValueError("Domain is needed in order to select the right config file.")
        fileName = domain
        configPaths = resolveConfigPath(fileName, f"{configType}/")
        SchemaClass = getattr(configModule, f"selectDomain")(domain)

    with open(configPaths[fileName]) as f:
        data = yaml.safe_load(f)
    return SchemaClass(**data)

def saveConfig(name, configPaths, configData):
    with open(configPaths[name], "w") as f:
        yaml.safe_dump(configData, f)