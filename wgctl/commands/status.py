import click

from wgctl.util.exec import run
from wgctl.util.cli import ok, error, fatal
from wgctl.util.config import get_config
from sys import exit

@click.command(help='shows if a tunnel is up')
@click.pass_context
@click.argument('instance', required=False)
def status(context, instance):
  if instance is None:
    return status_all(context)
  
  instance, config = get_config(instance)

  if not run(context, 'wg show {}'.format(instance), abort_on_error=False, silence=True):
    error('WireGuard interface is down.')
    exit(1)
  else:
    ok('WireGuard interface is up')

def status_all(context):
  (success, interfaces) = run(context, 'wg show interfaces', silence=True, return_output=True)
  if not success:
    fatal('could not retrieve WireGuard interfaces')

  for iface in iter(interfaces.split(' ')):
    if not iface.strip():
      continue
    
    _, config = get_config(iface.strip())
    description = iface
    if 'description' in config is not None:
      description = '{} ({})'.format(config['description'], iface.strip())

    ok(description)

@click.command(help='shows information on a particular tunnel')
@click.pass_context
@click.argument('instance')
def info(context, instance):
  instance, config = get_config(instance)

  if not run(context, 'wg show {}'.format(instance), abort_on_error=False, silence=True):
    error('WireGuard interface is down.')
    exit(1)
  
  run(context, 'wg show {}'.format(instance), silence=True, show_output=True, abort_on_error=False)