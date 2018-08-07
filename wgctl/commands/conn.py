import click

from wgctl.util.cli import ok, fatal, info
from wgctl.util.config import get_config
from wgctl.util.netlink import WireGuard
from wgctl.util.network import parse_net
from pyroute2 import IPRoute

@click.command(help='starts up a tunnel')
@click.pass_context
@click.argument('instance')
def up(context, instance):
  instance, config = get_config(instance)
  wg = WireGuard()

  if wg.device_exists(ifname=instance):
    fatal('WireGuard interface is already up.')
  
  with open(config['interface']['private_key']) as key:
    config['interface']['private_key'] = key.readline().strip()

  address, cidr = parse_net(config['interface']['address'])
  port = config['interface']['listen_port']
  pkey = config['interface']['private_key']
  fwmark = config['interface']['fwmark']
  peers = config['peers']

  ip = IPRoute()
  ip.link('add', ifname=instance, kind='wireguard')
  
  index = ip.link_lookup(ifname=instance)[0]
  
  ip.link('set', index=index, state='up')
  ip.addr('add', index=index, address=address, prefixlen=cidr)

  WireGuard().set_device(ifindex=index, listen_port=port, private_key=pkey, peers=peers, fwmark=fwmark)

  for peer in config['peers']:
    for aip in peer['allowed_ips']:
      if aip == '0.0.0.0/0':
        ip.route('add', dst='0.0.0.0/0', oif=index, table=port)
        ip.rule('add', table=254, FRA_SUPPRESS_PREFIXLEN=0, priority=18000)
        ip.rule('add', fwmark=port, fwmask=0, table=port, priority=20000)
      else:
        ip.route('add', dst=aip, oif=index)

  ok('WireGuard tunnel set up successfully')

@click.command(help='bring down a tunnel')
@click.pass_context
@click.argument('instance')
def down(context, instance):
  instance, config = get_config(instance)

  if not WireGuard().device_exists(ifname=instance):
    fatal('WireGuard interface is already down.')

  port = config['interface']['listen_port']

  ip = IPRoute()
  ip.link('delete', ifname=instance)

  nets = [peer['allowed_ips'] for peer in config['peers']]
  nets = [item for sublist in nets for item in sublist]

  if '0.0.0.0/0' in nets:
    try:
      ip.rule('delete', table=254, FRA_SUPPRESS_PREFIXLEN=0, priority=18000)
      ip.rule('delete', fwmark=port, fwmask=0, table=port, priority=20000)
    except:
      pass
  
  ok('WireGuard tunnel brought down successfully')

@click.command(help='restarts a tunnel (reloading its configuration)')
@click.pass_context
@click.argument('instance')
def downup(context, instance):
  context.invoke(down, instance=instance)
  context.invoke(up, instance=instance)
