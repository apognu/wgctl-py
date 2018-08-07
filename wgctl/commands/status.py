import click

from wgctl.util.cli import ok, error, fatal
from wgctl.util.config import get_config
from wgctl.util.netlink import WireGuard
from wgctl.util.network import format_key
from sys import exit
from colorama import Fore, Style

@click.command(help='shows if a tunnel is up')
@click.pass_context
@click.argument('instance', required=False)
def status(context, instance):
  if instance is None:
    return status_all(context)
  
  instance, _ = get_config(instance)

  if not WireGuard().device_exists(instance):
    error('WireGuard interface is down.')
    exit(1)
  else:
    ok('WireGuard interface is up')

def status_all(context):
  interfaces = WireGuard().get_devices()

  for iface in interfaces:
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
  interface = WireGuard().get_device_dict(ifname=instance)
  interface = interface[instance]

  output = f"""
{Style.BRIGHT}{Fore.RED}tunnel:{Style.RESET_ALL} {config['description']}
  {Style.DIM}interface:{Style.RESET_ALL} {instance}
  {Style.DIM}public key:{Style.RESET_ALL} {format_key(interface['public_key'])}
  {Style.DIM}listening port:{Style.RESET_ALL} {interface['listen_port']}
"""

  for peer in interface['peers']:
    key = format_key(peer['public_key'])
    peerconf = [peerconf for peerconf in config['peers'] if peerconf['public_key'] == key]
    
    description = '<no peer description>'
    if len(peerconf) > 0 and 'description' in peerconf[0]:
      description = peerconf[0]['description']

    output += f"""
  - {Style.BRIGHT}{Fore.GREEN}peer:{Style.RESET_ALL} {description}
      {Style.DIM}public key:{Style.RESET_ALL} {key}
      {Style.DIM}endpoint:{Style.RESET_ALL} {peer['endpoint'][0]}:{peer['endpoint'][1]}
      {Style.DIM}allowed ips:{Style.RESET_ALL} {', '.join(peer['allowedips'])}
      {Style.DIM}preshared key?{Style.RESET_ALL} {all(c == '0' for c in peer['preshared_key'].hex())}
"""

  print(output)

