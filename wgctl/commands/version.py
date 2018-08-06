import click

@click.command()
def version():
  click.echo('wgctl version 0.1')