import yaml
from pathlib import Path
from landserm.config.validators import isPath
from landserm.config.schemas import delivery, network, policies, services, storage

landserm_root = str(Path(__file__).resolve().parents[2])
config_path = landserm_root + "/landserm/domains/"
config_files = ["network.yaml", "services.yaml", "storage.yaml"]
config_files_path = {
    "network": None,
    "services": None,
    "storage": None
}

domains = []

for file in config_files:
    file_path = config_path + file
    domain = file[:-5]
    domains.append(domain)
    if isPath(file_path):
        config_files_path[domain] = file_path
    else:
        print(f"WARNING: {file} is not in config path: {config_path}")

def load_config(domain):
    with open(config_files_path[domain]) as f:
        return yaml.safe_load(f)

def save_config(domain, config_data):
    with open(config_files_path[domain], "w") as f:
        yaml.safe_dump(config_data, f)

def getSchema(name):
    switch = {
        "delivery": delivery.schema,
        "network": network.schema,
        "policies": policies.schema,
        "services": services.schema,
        "storage": storage.schema
    }
    return switch.get(name) 