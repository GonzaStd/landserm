import click
import questionary
from typing import Literal
from rich.pretty import Pretty
from landserm.config.system import *
from landserm.config.loader import loadConfig, saveConfig, loadSchemaClass
from landserm.cli.interactions import listEdit, getObjectAttribute, setObjectAttribute
import landserm.cli.completers as complete

def showConfig(configType: Literal["delivery", "domains", "policies"], domain: str = None):
    configType = configType.lower()

    if not domain:
        click.echo(f"{configType.capitalize()} config")

    if configType == "delivery":
        configObject = loadConfig(configType)
    else:
        if domain:
            click.echo(f"{configType.capitalize} config for {domain.upper()}")
            configObject = loadConfig(configType, domain.lower())
        else:
            for domain in complete.DOMAIN_NAMES:
                click.echo(f"DOMAIN: {domain.capitalize()}")
                configObject = loadConfig("domains", domain.lower())

    click.echo(Pretty(configObject.model_dump(), expand_all=True))

def listConfig(configType: Literal["delivery", "domains", "policies"], domain: str = None):
    configType = configType.lower()
    if not domain:
        click.echo(complete.DOMAIN_NAMES)
    else:
        dictConfig = loadConfig(configType, domain).model_dump()
        click.echo(dictConfig.keys())

def editConfig(configType: Literal["delivery", "domains", "policies"], field, domain: str = None):
    """
    Edit any type of configuration.

    Examples:
        landserm config <domains|policies> edit --domain services
        landserm config delivery edit oled.driver
    """
    try:
        configObject = loadConfig(configType, domain)

        value = getObjectAttribute(configObject, path=field)

        if not field:
            click.echo("Available fields (navigate inside them with dot notation if field is a dict):")
            schemaClass = loadSchemaClass(configType, domain)
            for key in schemaClass.model_fields.keys():
                click.echo(f"   - {key}")
            return
        
        if isinstance(value, list):
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
            elif newValue.strip == "":
                newValue = value
            else:
                raise ValueError(f"{newValue} value is invalid. Please choose between True and False (your field is a boolean)")
        
        else:
            newValue = questionary.text(f"New value").ask()

        newConfig = setObjectAttribute(configObject, path=field, newValue=newValue)
        saveConfig(configType, newConfig, domain)
        click.echo("Config saved")
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
@click.option("--domain", required=False, autocompletion=complete.domains)
def show(domain: str = None):
    showConfig("policies", domain)

@policies.command()
@click.option("--domain", required=True, autocompletion=complete.domains)
def list(domain: str):
    listConfig("policies", domain)

@policies.command()
@click.option("--domain", required=True, autocompletion=complete.domains)
@click.argument("field", required=False)
def edit(domain: str, field: str = None):
    editConfig("policies", field, domain)

# DELIVERY CONFIG

@config.group()
def delivery():
    """Manage settings for each delivery method (push urls, OLED properties, etc)"""
    pass

@delivery.command()
@click.option("--method", required=False, autocompeltion=complete.deliveryMethods)
def show(method: str = None):
    if not method:
        showConfig("delivery")
    else:
        dictConfig = loadConfig("delivery").model_dump()
        click.echo(f"Delivery config for {method}")
        click.echo(Pretty(dictConfig.get(method)))

@delivery.command()
@click.option("--method", required=False, autocompeltion=complete.deliveryMethods)
def list(method: str = None):
    if not method:
        click.echo(complete.DELIVERY_METHODS)
    else:
        for modelMethod, fieldInfo in delivery.DeliveryConfig.model_fields.items():
            if modelMethod == method:
                click.echo(fieldInfo.annotation.model_fields.keys()) 

@delivery.command()
@click.argument("field", required=False)
def edit(domain: str, field: str = None):
    editConfig("delivery", field, domain)


# DOMAINS CONFIG

@config.group()
def domains():
    """Manage settings for each domain. (services you want to listen to)"""
    pass

@domains.command()
@click.option("--domain", required=False, autocompletion=complete.domains)
def show(domain: str = None):
    showConfig("domains", domain)

@domains.command()
@click.option("--domain", required=False, autocompletion=complete.domains)
def list(domain: str = None):
    listConfig("domains", domain)

@domains.command()
@click.option("--domain", required=True, autocompletion=complete.domains)
@click.argument("field", required=False)
def edit(domain: str, field: str = None):
    editConfig("domains", field, domain)