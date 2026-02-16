import click
import sys
import traceback

@click.group()
@click.option("--debug", is_flag=True, help="Show full traceback on errors")
@click.pass_context
def cli(ctx, debug):
    """Landserm CLI"""
    ctx.ensure_object(dict)
    ctx.obj['debug'] = debug

from landserm.cli.config import config
cli.add_command(config)

@cli.result_callback()
@click.pass_context
def handle_result(ctx, *args, **kwargs):
    pass

if __name__ == "__main__":
    try:
        cli()
    except Exception as e:
        ctx = click.get_current_context() if click.get_current_context() else None
        debug = ctx.obj.get('debug', False) if ctx and ctx.obj else False
        
        click.echo(f"Error: {e}", err=True)
        if debug:
            click.echo("\nTraceback:", err=True)
            traceback.print_exc()
        sys.exit(1)