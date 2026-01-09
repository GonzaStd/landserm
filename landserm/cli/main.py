import click

@click.group()
def cli():
    pass

from landserm.cli.config import config
cli.add_command(config)