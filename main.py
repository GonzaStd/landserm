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
        subprocess.run(["lsblk", "-o", "NAME,SIZE,PARTUUID,MOUNTPOINTS"],
        capture_output=True,
        text=True,
        check=True).stdout
    )

def show_services():
    print("For the next question, consider your terminal buffer size.")
    a = input("¿Do you want to see your services? y to proceed, any keyword to skip: ") 
    if (a.lower == "y"):
        print("This are your services (systemctl list-unit-files")
        print(
            subprocess.run(["systemctl", "list-unit-files"],
            capture_output=True,
            text=True,
            check=True).stdout
        )
    pass

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

def parse_value(value: str, expected_type): 
    """ It returns valid values to store in yaml, and invalid values to display, 
    so the user can now what he did wrong.
    """
    valid_values = []
    invalid_values = []
    inner_type = ""
    # BOOL
    switch_bool = {
        "true": True,
        "false": False
    }
    
    if (expected_type == "bool"):
        value = value.lower()
        parsed = switch_bool.get(value, None)
        if (parsed != None):
            valid_values.append(parsed)

    # LIST
    elif (expected_type.startswith("list")):
        switch_list = {
        "partuuid": isPartuuid,
        "path": isPath,
        "service_name": isService
        }
        inner_type = expected_type[5:-1]
        values_list = value.split(",")
        for i in values_list:
            if (switch_list.get(inner_type)(i)):
                valid_values.append(i)
            else:
                invalid_values.append(i)

    return valid_values, invalid_values, str(inner_type)
        

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
    keys_l = keys.split(".") # A list of all the keys (indeed the path) to the config parameter/field.
    schema_path = schema # Here is the whole schema, that's were we start
    for key in keys_l:
        schema_path = schema_path[key] # This goes through each key that leads us to the configuration field
    # Finally, we have the schema of the property.

    field_type = schema_path["type"] # We access the type that this field should receive
    parsed_values, invalid_values, inner_type = parse_value(value, field_type)
    config_mod = config_data # Here will remain the data we'll modify.
    for key in keys_l[:-1]: # This goes through each key except the last one
        config_mod = config_mod[key]
    """
    We need the last key to mutate the field from the same tree
    otherwise we would have copy the value from the field to a new variable
    and rewrite the new variable with a new value (useless)
    """
    last_key = keys_l[-1]
    if (field_type == "bool"):
        if (len(parsed_values)==1):
            config_mod[last_key] = parsed_values[0]
        else:
            print("Invalid value, you should use true/false instead.")

    if (field_type.startswith("list")):
            if (invalid_values):
                print(f"This values were invalid and aren't saved: {str(invalid_values)[1:-1]}")

                if (inner_type == "partuuid"):
                    show_partitions()

                if (inner_type == "service"):
                    show_services()

            if (inner_type == "path"):
                absolute_paths = []
                for path in parsed_values:
                    absolute_paths.append(os.path.abspath(path))
                parsed_values = absolute_paths
            
            config_mod[last_key] = parsed_values
    with open("./config.yaml", "w") as config_file:
        yaml.safe_dump(config_data, config_file)
    

if __name__ == "__main__":
    cli()