# This will be necessary for version 2, because new domains handling will be added.
import yaml
import importlib
from dotenv import load_dotenv
from os import environ as env
from os import path as osPath
from pathlib import Path
from typing import Union, Type, Literal
from landserm.config.validators import isPath
from landserm.config.schemas import delivery, domains, policies
from landserm.core.logger import getLogger

DOMAIN_NAMES = ["services"]

logger = getLogger(context="config")

# Load environment variables once
_env_loaded = False

def loadEnvironment():
    """Load environment variables from .env file. Called automatically on first import."""
    global _env_loaded
    
    if _env_loaded:
        return
    
    if env.get("_LANDSERM_COMPLETE"):
        _env_loaded = True
        return
    
    env_paths = [
        Path("/etc/landserm/.env"),
        Path.home() / ".landserm" / ".env",
        Path.cwd() / ".env"
    ]
    
    for env_file in env_paths:
        try:
            if env_file.exists():
                load_dotenv(env_file)
                print("\n")
                logger.info(f"Loaded env from {env_file}")
                _env_loaded = True
                return
        except PermissionError:
            logger.error(f"No permission to read {env_file}. Skipping.")
            continue
    
    logger.warning("No .env file found, using defaults")
    _env_loaded = True

# Load environment on module import
loadEnvironment()

landsermRoot = str(Path(__file__).resolve().parents[2])
defaultConfigBase = landsermRoot + "/config-template/"
chosenConfigBase = env.get("LANDSERM_CONFIG_PATH", defaultConfigBase)

def resolveConfigPath(fileNames: list | str, configTailFolder: str = "") -> dict: 
    if osPath.isdir(chosenConfigBase):
        configBase = chosenConfigBase
    else:
        logger.warning(f"Your base config ({chosenConfigBase}) does not exist")
        logger.info(f"Using {defaultConfigBase}")
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
            logger.warning(f"{file} is not in path: {configFolderPath}")
    return filesPath
        
def loadSchemaClass(configType: Literal["delivery", "domains", "policies"], domain: str = None, getConfig: bool = False)-> Type[Union[delivery.DeliveryConfig, domains.domainsConfig, policies.domainsPolicy]]:
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
    if not getConfig:
        return SchemaClass
    else:
        return SchemaClass, configPaths, fileName

def loadConfig(configType: Literal["delivery", "domains", "policies"], domain: str = None) -> Union[delivery.DeliveryConfig, domains.domainsConfig, policies.domainsPolicy]:
  
    if domain and domain not in DOMAIN_NAMES:
        raise ValueError(f"Invalid domain: {domain}. Valid domains are: {', '.join(DOMAIN_NAMES)}")
    
    SchemaClass, configPaths, fileName = loadSchemaClass(configType, domain, getConfig=True)

    with open(configPaths[fileName]) as f:
        data = yaml.safe_load(f)
    
    return SchemaClass(**data)

def loadConfigRaw(configType: Literal["delivery", "domains", "policies"], domain: str = None) -> dict:
    if configType == "delivery":
        fileName = configType
        configPaths = resolveConfigPath(fileName)
    elif configType in ["domains", "policies"]:
        if not domain:
            raise ValueError("Domain needed")
        fileName = domain
        configPaths = resolveConfigPath(fileName, f"{configType}/")
    
    with open(configPaths[fileName]) as f:
        return yaml.safe_load(f)

def saveConfig(configType: Literal["delivery", "domains", "policies"], 
               configData: Type[Union[delivery.DeliveryConfig, domains.domainsConfig, policies.domainsPolicy]],
               domain: str = None):
    
    if configType == "delivery":
        fileName = configType
        configPaths = resolveConfigPath(fileName)
    elif configType in ["domains", "policies"]:
        if not domain:
            raise ValueError("Domain needed for saving")
        fileName = domain
        configPaths = resolveConfigPath(fileName, f"{configType}/")
    else:
        raise ValueError(f"Unknown config type: {configType}")
    
    # Convertir Pydantic a dict
    if hasattr(configData, 'model_dump'):
        data = configData.model_dump()
    else:
        if isinstance(configData, dict): # This should be a dict
            data = configData 
    
    with open(configPaths[fileName], "w") as f:
        yaml.safe_dump(data, f)