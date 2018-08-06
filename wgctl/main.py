import click

from os import getuid
from wgctl.util.cli import fatal

from wgctl.commands import \
  version, \
  conn, \
  status

@click.group()
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