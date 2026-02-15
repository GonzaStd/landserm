import json
import click
from rich.pretty import Pretty
from landserm.config.system import *
from landserm.config.loader import loadConfig, saveConfig
import landserm.cli.completers as complete

def showConfig(configType: str, domain: str = None):
    configType = configType.lower()

    if not domain:
        click.echo(f"{configType.capitalize()} config")

    if configType == "delivery":
        configData = loadConfig(configType)
    else:
        if domain:
            click.echo(f"{configType.capitalize} config for {domain.upper()}")
            configData = loadConfig(configType, domain.lower())
        else:
            for domain in complete.DOMAIN_NAMES:
                click.echo(f"DOMAIN: {domain.capitalize()}")
                configData = loadConfig("domains", domain.lower())

    click.echo(Pretty(configData.model_dump(), expand_all=True))

def listConfig(configType: str, domain: str = None):
    configType = configType.lower()
    if not domain:
        click.echo(complete.DOMAIN_NAMES)
    else:
        dictConfigData = loadConfig(configType, domain).model_dump()
        click.echo(dictConfigData.keys())
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
        dictConfigDelivery = loadConfig("delivery").model_dump()
        click.echo(f"Delivery config for {method}")
        click.echo(Pretty(dictConfigDelivery.get(method)))

@delivery.command()
@click.option("--method", required=False, autocompeltion=complete.deliveryMethods)
def list(method: str = None):
    if not method:
        click.echo(complete.DELIVERY_METHODS)
    else:
        dictConfigDelivery = loadConfig("delivery").model_dump()
        click.echo(dictConfigDelivery.get(method).keys())


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