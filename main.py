import click, yaml, subprocess
from rich import print
from rich.pretty import Pretty
import os

schema = {
    'storage': {
        'backup': {
            "enabled": {
                "type": "bool",
                "nullable": False
            },
            "repositories": {
                "type": "list[path]",
                "nullable": True
            }
        },

        'space': {
            "enabled": {
                "type": "bool",
                "nullable": False
            },
            "partitions": {
                "type": "list[partuuid]",
                "nullable": True
            }
        },

        'mount': {
            "enabled": {
                "type": "bool",
                "nullable": False
            },
            "partitions": {
                "type": "list[partuuid]",
                "nullable": True
            }
        }
    },
    'services': {
        'enabled':  {
            "type": "bool",
            "nullable": False
        },
        'include': {
                "type": "list[service_name]",
                "nullable": True
            }
    }
}

def show_partitions():
    print("This are your partitions and devices, check at the PARTUUID (lsblk -o NAME,SIZE,PARTUUID,MOUNTPOINTS)")
    print(
        subprocess.run(["lsblk"] ["-o"] ["NAME,SIZE,PARTUUID,MOUNTPOINTS"],
        capture_output=True,
        text=True,
        check=True).stdout
    )

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

def parse_value(value: str, expected_type):
    switch_bool = {
        "true": True,
        "false": False
    }

    switch_list = {
        "partuuid": isPartuuid,
        "path": isPath,
        "service_name": isService
    }

    
    if (expected_type == "bool"):
        value = value.lower()
        parsed = switch_bool.get(value, None)
        if (parsed != None):
            return parsed

    elif (expected_type.startswith("list")):
        inner_type = expected_type[5:-1]
        values_list = value.split(" ")
        valid_values = []
        invalid_values = []
        for i in values_list:
            if (switch_list.get(inner_type)(i)):
                valid_values.append(i)
            else:
                invalid_values.append(i)
        
        if (invalid_values): # This is for any
            print(f"This values were invalid and aren't saved: {' '.join(str(invalid_values)[1:-1])}")
            # This is for PARTUUIDs
            if (inner_type == "partuuid"):
                show_partitions()

        # This is for PATHS
        if (inner_type == "path"):
            absolute_paths = []
            for path in valid_values:
                absolute_paths.append(os.path.abspath(path))
            return absolute_paths

        return valid_values
        

with open("config.yaml", "r") as file:
    config_data = yaml.safe_load(file)

@click.group()
def cli():
    pass

@cli.group()
def config():
    pass

@cli.command()
@click.argument("option", required=True)
def show(option):
    if (option == "partitions"):
        show_partitions()

@config.command()
@click.argument("category", required=False)
def show(category: str = None):
    if category:
        category = category.lower()
        print(category.upper())
        print(Pretty(config_data[category], expand_all=True))
    else:
        print(Pretty(config_data, expand_all=True))

@config.command()
@click.argument("keys", required=True)
@click.argument("value", required=True)
def set(keys, value):
    keys_l = keys.split(".")
    schema_path = schema
    for key in keys_l:
        schema_path = schema_path[key]
    if (schema_path["type"] == "bool"):
        if (type(value) == bool):
            config
    print(schema_path)

if __name__ == "__main__":
    cli()