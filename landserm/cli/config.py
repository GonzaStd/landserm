import click, yaml
from rich import print
from rich.pretty import Pretty
from os.path import abspath
from landserm.config.system import *
from landserm.semantics.types import parse_value
from landserm.config.loader import getSchema, load_config, save_config, domains

@click.group()
def config():
    pass

@config.command()
@click.argument("domain", required=False)
@click.argument("unit", required=False)
def show(domain: str = None, unit: str = None):
    if domain:
        domain = domain.lower()
        print(domain.upper())
        config_data = load_config(domain)
        print(Pretty(config_data, expand_all=True))
    else:
        for domain in domains:
            config_data = load_config(domain)
            print(Pretty(config_data, expand_all=True))

@config.command()
@click.argument("key_path", required=True)
@click.argument("value", required=True)
def set(key_path, value):
    keys = key_path.split(".") # A list of all the keys (indeed the path) to the config parameter/field.
    domain = keys[0]
    config_data = load_config(domain)
    config_mod =  config_data # Here will remain the data we'll modify.
    schema_path = getSchema(domain) # Here is the whole schema, that's were we start
    for key in keys[1:]: # This goes through each key except the first one (the domain)
        schema_path = schema_path[key] # This goes through each key that leads us to the configuration field
    # Finally, we have the schema of the property.

    field_type = schema_path["type"] # We access the type that this field should receive
    parsed_values, invalid_values, inner_type = parse_value(value, field_type)
    for key in keys[:-1]: # This goes through each key except the last one
        config_mod = config_mod[key]
    """
    We need the last key to mutate the field from the same tree
    otherwise we would have copy the value from the field to a new variable
    and rewrite the new variable with a new value (useless)
    """
    last_key = keys[-1]
    if (field_type == "bool"):
        if (len(parsed_values)==1):
            config_mod[last_key] = parsed_values[0]
        else:
            print("Invalid value, you should use true/false instead.")

    if (field_type.startswith("list")):
            if (invalid_values):
                print(f"This values were invalid and aren't saved: {str(invalid_values)[1:-1]}")

                if (inner_type == "partuuid"):
                    getPartitions()

                if (inner_type == "service"):
                    print("For the next question, consider your terminal buffer size.")
                    a = input("¿Do you want to see your services? y to proceed, any keyword to skip: ") 
                    if (a.lower == "y"):
                        print("This are your services (systemctl list-unit-files")
                        print(getServices())

            if (inner_type == "path"):
                absolute_paths = []
                for path in parsed_values:
                    absolute_paths.append(abspath(path))
                parsed_values = absolute_paths
            config_mod[last_key] = parsed_values
            
    save_config(domain, config_data)