import click, yaml
from rich import print
from rich.pretty import Pretty
from os.path import abspath
from landserm.config.system import *
from landserm.semantics.types import parse_value
from landserm.config.loader import domainsConfigPaths, loadConfig, saveConfig, getSchema, domains

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
        configData = loadConfig(domain, domainsConfigPaths)
        print(Pretty(configData, expand_all=True))
    else:
        for domain in domains:
            configData = loadConfig(domain, domainsConfigPaths)
            print(Pretty(configData, expand_all=True))

@config.command()
@click.argument("key_path", required=True)
@click.argument("value", required=True)
def set(key_path, value):
    keys = key_path.split(".") # A list of all the keys (indeed the path) to the config parameter/field.
    domain = keys[0]
    keys = keys[1:] # domain key removed.

    configData = loadConfig(domain, domainsConfigPaths)
    configMod =  configData # Here will remain the data we'll modify.

    schemaPath = getSchema(domain) # Here is the whole schema, that's were we start
    for key in keys:
        schemaPath = schemaPath[key] # This goes through each key that leads us to the configuration field
    fieldType = schemaPath["type"] # We access the type that this field should receive
    parsedValues, invalidValues, innerType = parse_value(value, fieldType)

    for key in keys[:-1]: # This goes through each key except the the last one
        configMod = configMod[key]
    """
    We need the last key to mutate the field from the same tree
    otherwise we would have copy the value from the field to a new variable
    and rewrite the new variable with a new value (useless)
    """
    lastKey = keys[-1]
    if (fieldType == "bool"):
        if (len(parsedValues)==1):
            configMod[lastKey] = parsedValues[0]
        else:
            print("Invalid value, you should use true/false instead.")

    if (fieldType.startswith("list")):
            if (invalidValues):
                print(f"This values were invalid and aren't saved: {str(invalidValues)[1:-1]}")

                if (innerType == "partuuid"):
                    getPartitions()

                if (innerType == "service"):
                    print("For the next question, consider your terminal buffer size.")
                    a = input("¿Do you want to see your services? y to proceed, any keyword to skip: ") 
                    if (a.lower == "y"):
                        print("This are your services (systemctl list-unit-files)")
                        print(getServicesData())

            if (innerType == "path"):
                absolutePaths = []
                for path in parsedValues:
                    absolutePaths.append(abspath(path))
                parsedValues = absolutePaths
            configMod[lastKey] = parsedValues
            
    saveConfig(domain, domainsConfigPaths, configData)