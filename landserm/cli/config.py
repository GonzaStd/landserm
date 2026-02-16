import click
import questionary
from typing import Literal
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
        configDict = loadConfigRaw(configType, domain)

        if not field:
            if configType == "policies":
                # Show available policies
                click.echo("Available policies:")
                policyNames = list(configDict.keys())
                for policyName in policyNames:
                    click.echo(f"   - {policyName}")
                click.echo("\nUsage: landserm config policies edit --domain <domain> <policy-name>.<field>")
                click.echo("Examples:")
                click.echo("   landserm config policies edit --domain services policy-name.enabled")
                click.echo("   landserm config policies edit --domain services policy-name.then.priority")
            else:
                # Show schema fields
                click.echo("Available fields (navigate inside them with dot notation if field is a dict):")
                schemaClass = loadSchemaClass(configType, domain) # This is not supposed to validate
                for key in schemaClass.model_fields.keys():
                    click.echo(f"   - {key}")
            return
        
        value = getValueByPath(configDict, path=field)

        newValue = None
        
        if isinstance(value, list):
            newValue = listEdit(value)

        elif isinstance(value, bool):
            options = ["true", "t", "false", "f"]
            newValue = str(questionary.text(f"Choose boolean (True or False) for {field} [{value}]:").ask()).lower()
            if newValue in options:
                index = options.index(newValue)
                newValue = True if index <= 1 else False
            elif newValue.strip() == "":
                newValue = value
            else:
                raise ValueError(f"\"{newValue}\" value is invalid. Please choose between True and False")
        elif isinstance(value, dict):
            click.echo(f"\"{field}\" is a dictionary. Your path should follow some of this: ")
            for key in value:
                click.echo(f" .{key}")
        elif isinstance(value, str):
            answer = str(questionary.text(f"Enter the new value for {field} [{value}]").ask())
            newValue = value if answer.strip() == "" else answer
        
        if newValue is None:
            raise ValueError(f"Couldn't find method to modify this keypath field: {field}\n Its type is: {type(value)}")

        newConfigDict = setValueByPath(configDict, path=field, newValue=newValue)

        # VALIDATION

        try:
            schemaClass = loadSchemaClass(configType, domain)
            schemaClass(**newConfigDict)
        except Exception as validationError:
            raise ValueError(f"Validation error: {validationError}")

        saveConfig(configType, newConfigDict, domain)
        click.echo(f"Changed from {value} to {newValue}. Config saved.")
    except Exception as e:
        click.echo(f"Edit config error: {e}")

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

@policies.command(name="list")
@click.option("--domain", required=True, shell_complete=complete.domains)
def listPolicies(domain: str):
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

@delivery.command(name="list")
@click.option("--method", required=False, shell_complete=complete.deliveryMethods)
def listDelivery(method: str = None):
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

@domains.command(name="list")
@click.option("--domain", required=False, shell_complete=complete.domains)
def listDomains(domain: str = None):
    listConfig("domains", domain)

@domains.command()
@click.option("--domain", required=True, shell_complete=complete.domains)
@click.argument("field", required=False)
def edit(domain: str, field: str = None):
    editConfig("domains", field, domain)