import click
import questionary
from typing import Literal, List
from rich.pretty import pprint
from landserm.config.system import *
from landserm.config.loader import loadConfigRaw, saveConfig, loadSchemaClass
from landserm.cli.interactions import listEdit, getValueByPath, setValueByPath
import landserm.cli.completers as complete

def showConfig(configType: Literal["delivery", "domains", "policies"], domain: str = None):
    configType = configType.lower()

    if not domain:
        click.echo(f"{configType.capitalize()} config")

    if configType == "delivery":
        configDict = loadConfigRaw(configType)
    else:
        if domain:
            click.echo(f"{configType.capitalize()} config for {domain.upper()}")
            configDict = loadConfigRaw(configType, domain.lower())
        else:
            for domain in complete.DOMAIN_NAMES:
                click.echo(f"DOMAIN: {domain.capitalize()}")
                configDict = loadConfigRaw(configType, domain.lower())

    pprint(configDict, expand_all=True)

def listConfig(configType: Literal["delivery", "domains", "policies"], domain: str = None):
    configType = configType.lower()
    if not domain:
        click.echo(complete.DOMAIN_NAMES)
    else:
        configDict = loadConfigRaw(configType, domain)
        click.echo(configDict.keys())

def editConfig(configType: Literal["delivery", "domains", "policies"], field, domain: str = None):
    """
    Edit any type of configuration.

    Examples:
        landserm config <domains|policies> edit --domain services
        landserm config delivery edit oled.driver
    """
    try:
        if not field:
            click.echo("Available fields (navigate inside them with dot notation if field is a dict):")
            schemaClass = loadSchemaClass(configType, domain)
            for key in schemaClass.model_fields.keys():
                click.echo(f"   - {key}")
            return
        
        configDict = loadConfigRaw(configType, domain)

        value = getValueByPath(configDict, path=field)

        
        if isinstance(value, List):
            newValue = listEdit(value)

        elif isinstance(value, bool):
            options = ["true", "t", "false", "f"]
            newValue = str(questionary.text(f"Choose boolean (True or False) for {field} [{value}]").ask()).lower()
            if newValue in options:
                index = options.index(newValue)
                if index <= 1:
                    newValue = True
                elif index >= 2:
                    newValue = False
            if newValue.strip() == "":
                newValue = value
            else:
                raise ValueError(f"\"{newValue}\" value is invalid. Please choose between True and False (your field is a boolean)")
        
        else:
            newValue = questionary.text(f"New value").ask()

        newConfigDict = setValueByPath(configDict, path=field, newValue=newValue)
        saveConfig(configType, newConfigDict, domain)
        click.echo(f"Changed from {value} to {newValue}. Config saved.")
    except Exception as e:
        click.echo(f"Error: {e}")

# ROOT

@click.group()
def config():
    """Manage config for domains, policies or delivery methods."""
    pass

# POLICIES CONFIG

@config.group()
def policies():
    """Manage policies for each domain"""
    pass

@policies.command()
@click.option("--domain", required=False, shell_complete=complete.domains)
def show(domain: str = None):
    showConfig("policies", domain)

@policies.command()
@click.option("--domain", required=True, shell_complete=complete.domains)
def list(domain: str):
    listConfig("policies", domain)

@policies.command()
@click.option("--domain", required=True, shell_complete=complete.domains)
@click.argument("field", required=False)
def edit(domain: str, field: str = None):
    editConfig("policies", field, domain)

# DELIVERY CONFIG

@config.group()
def delivery():
    """Manage settings for each delivery method (push urls, OLED properties, etc)"""
    pass

@delivery.command()
@click.option("--method", required=False, shell_complete=complete.deliveryMethods)
def show(method: str = None):
    if not method:
        showConfig("delivery")
    else:
        configDict = loadConfigRaw("delivery")
        click.echo(f"Delivery config for {method}")
        pprint(configDict.get(method), expand_all=True)

@delivery.command()
@click.option("--method", required=False, shell_complete=complete.deliveryMethods)
def list(method: str = None):
    if not method:
        click.echo(complete.DELIVERY_METHODS)
    else:
        for modelMethod, fieldInfo in delivery.DeliveryConfig.model_fields.items():
            if modelMethod == method:
                click.echo(fieldInfo.annotation.model_fields.keys()) 

@delivery.command()
@click.argument("field", required=False)
def edit(field: str = None):
    editConfig("delivery", field)


# DOMAINS CONFIG

@config.group()
def domains():
    """Manage settings for each domain. (services you want to listen to)"""
    pass

@domains.command()
@click.option("--domain", required=False, shell_complete=complete.domains)
def show(domain: str = None):
    showConfig("domains", domain)

@domains.command()
@click.option("--domain", required=False, shell_complete=complete.domains)
def list(domain: str = None):
    listConfig("domains", domain)

@domains.command()
@click.option("--domain", required=True, shell_complete=complete.domains)
@click.argument("field", required=False)
def edit(domain: str, field: str = None):
    editConfig("domains", field, domain)