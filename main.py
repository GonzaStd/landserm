import click, yaml
from rich import print
from rich.pretty import Pretty

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
                "type": "list[part-uuid]",
                "nullable": True
            }
        },

        'mount': {
            "enabled": {
                "type": "bool",
                "nullable": False
            },
            "partitions": {
                "type": "list[part-uuid]",
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

def parse_value(value: str, expected_type):
    switch_bool = {
        "true": True,
        "false": False
    }

    switch_list = {
        "part_uuid": validate_partuuid,
        "path": validate_path,
        "service_name": validate_service
    }

    
    if (expected_type == "bool"):
        value = value.lower()
        parsed = switch_bool.get(value, None)
        if (parsed != None):
            return parsed

    elif (expected_type.startswith("list")):
        inner_type = expected_type[5:-1]
        values_list = values.split(" ")
        valid_values = []
        for i in value_list:
            if (switch_list.get(inner_type)(i)):
                valid_values.append(i)
        return valid_values
        

with open("config.yaml", "r") as file:
    config_data = yaml.safe_load(file)

@click.group()
def cli():
    pass

@cli.group()
def config():
    pass

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