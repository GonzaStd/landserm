"""
import click
from landserm.config.system import *

@cli.command()
@click.argument("option", required=True)
def show(option):
    if (option == "partitions"):
        print("This are your partitions and devices, check at the PARTUUID (lsblk -o NAME,SIZE,PARTUUID,MOUNTPOINTS)")
        print(getPartitions())
"""