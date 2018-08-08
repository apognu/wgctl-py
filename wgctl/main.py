import click

from os import getuid
from wgctl.util.cli import fatal
from base64 import b64encode

from wgctl.commands import \
  version, \
  conn, \
  status

CONTEXT_SETTINGS=dict(help_option_names=['-h', '--help'])

@click.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
@click.option('--verbose', '-v', is_flag=True, default=False)
def main(context, verbose):
  context.obj = {
    'verbose': verbose
  }

  pass

if getuid() > 0:
  fatal('this should be run as root')

main.add_command(version.version)
main.add_command(conn.up)
main.add_command(conn.down)
main.add_command(conn.downup)
main.add_command(status.status)
main.add_command(status.info)
