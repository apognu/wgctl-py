import click
import timeago

from glob import glob
from wgctl.util.cli import ok, error, fatal, dim
from wgctl.util.config import get_config
from wgctl.util.netlink import WireGuard
from wgctl.util.network import format_key
from sys import exit
from colorama import Fore, Style
from datetime import datetime

@click.command(help='shows if a tunnel is up')
@click.pass_context
@click.argument('instance', required=False)
def status(context, instance):
  if instance is None:
    return status_all(context)
  
  instance, _ = get_config(instance)

  if not WireGuard().device_exists(instance):
    error('tunnel interface is down.')
    exit(1)
  else:
    ok('tunnel interface is up', symbol='↑')

def status_all(context):
  interfaces = WireGuard().get_devices()

  for iface in interfaces:
    if not iface.strip():
      continue
    
    _, config = get_config(iface.strip())
    description = iface
    if 'description' in config is not None:
      description = '{} ({})'.format(config['description'], iface.strip())

    ok(description, symbol='↑')

  for file in glob('/etc/wireguard/*.yml'):
    instance, config = get_config(file)

    if config is not None and not instance in interfaces:
      description = instance
      if 'description' in config:
        description = '{} ({})'.format(config['description'], instance)
      
      dim(description, symbol='↓')
    

@click.command(help='shows information on a particular tunnel')
@click.pass_context
@click.argument('instance')
def info(context, instance):
  wg = WireGuard()

  if not wg.device_exists(instance):
    fatal('device does not exist')

  instance, config = get_config(instance)
  interface = WireGuard().get_device_dict(ifname=instance)
  interface = interface[instance]

  fwmark = None
  if interface['fwmark'] > 0:
    fwmark = interface['fwmark']

  attrs = [
    attr('interface:', instance),
    attr('public key:', format_key(interface['public_key'])),
    attr('listening port:', interface['listen_port']),
    attr('fwmark:', fwmark)
  ]

  output = print_tunnel(config.get('description', '<no tunnel description>'))
  output += ''.join([line for line in attrs if line is not None])

  for peer in interface.get('peers', []):
    output += '\n'
    
    key = format_key(peer['public_key'])
    peerconf = [peerconf for peerconf in config['peers'] if peerconf['public_key'] == key]
    
    description = '<no peer description>'
    if len(peerconf) > 0 and 'description' in peerconf[0]:
      description = peerconf[0]['description']

    endpoint = None
    if peer.get('endpoint'):
      endpoint = '{}:{}'.format(peer['endpoint'][0], peer['endpoint'][1])

    allowed_ips = None
    if peer.get('allowedips'):
      allowed_ips = ', '.join(peer['allowedips'])

    if peer['last_handshake_time'].year == 1970:
      handshake = None
    else:
      handshake = timeago.format(peer['last_handshake_time'], datetime.now())

    if peer['persistent_keepalive_interval'] > 0:
      keepalive = f'Every {peer["persistent_keepalive_interval"]}s'
    else:
      keepalive = None

    rx_bytes = peer['rx_bytes']
    tx_bytes = peer['tx_bytes']
    traffic = rx_bytes + tx_bytes

    attrs = [
      attr('public key:', key, pad=4),
      attr('endpoint:', endpoint, pad=4),
      attr('allowed ips:', allowed_ips, pad=4),
      attr('preshared key?', not all(c == '0' for c in peer['preshared_key'].hex()), pad=4),
      attr('last handshake:', handshake, pad=4),
      attr('persistent keepalive:', keepalive, pad=4),
      attr('transfer:', f'↓ {rx_bytes} B ↑ {tx_bytes} B', rx_bytes + tx_bytes > 0, pad=4)
    ]

    output += print_peer(description)
    output += ''.join([line for line in attrs if line is not None])

  print(output)

def print_tunnel(description):
  return f'{Style.BRIGHT}{Fore.RED}tunnel:{Style.RESET_ALL} {description}\n'

def print_peer(description):
  return f'  - {Style.BRIGHT}{Fore.GREEN}peer:{Style.RESET_ALL} {description}\n'

def attr(key, value, condition=True, pad=0):
  if value is not None and condition:
    return f'{pad * " "}{Style.DIM}{key}{Style.RESET_ALL} {value}\n'
  
  return ''
