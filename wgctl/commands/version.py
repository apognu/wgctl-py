import click
import pkg_resources

@click.command()
def version():
  info = pkg_resources.require('wgctl')[0]

  click.echo('{} version {}'.format(info.project_name, info.version))
  click.echo('Copyright © 2018 Antoine POPINEAU')
  click.echo('Licence MIT')