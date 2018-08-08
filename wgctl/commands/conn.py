import click

from wgctl.util.cli import ok, fatal, info
from wgctl.util.config import get_config
from wgctl.util.netlink import WireGuard
from wgctl.util.network import parse_net
from pyroute2 import IPRoute

@click.command('start', help='starts up a tunnel')
@click.pass_context
@click.argument('instance')
def up(context, instance):
  instance, config = get_config(instance)
  wg = WireGuard()

  if wg.device_exists(ifname=instance):
    fatal('tunnel interface is already up.')
  
  try:
    with open(config['interface']['private_key']) as key:
      config['interface']['private_key'] = key.readline().strip()
  except Exception:
    fatal('could not read private key file')

  port = config['interface']['listen_port']
  fwmark = config['interface'].get('fwmark')

  address, cidr = None, None
  if config['interface'].get('address') is not None:
    address, cidr = parse_net(config['interface']['address'])

  ip = IPRoute()
  try:
    ip.link('add', ifname=instance, kind='wireguard')
  except Exception as e:
    fatal('could not create device: {}'.format(e))
  
  index = ip.link_lookup(ifname=instance)[0]
  ip.link('set', index=index, state='up')
  
  if address is not None and cidr is not None:
    ip.addr('add', index=index, address=address, prefixlen=cidr)

  WireGuard().set_device(ifindex=index, config=config)

  for peer in config['peers']:
    if peer.get('allowed_ips'):
      for aip in peer['allowed_ips']:
        try:
          if aip == '0.0.0.0/0':
            ip.route('add', dst='0.0.0.0/0', oif=index, table=port)
            ip.rule('add', table=254, FRA_SUPPRESS_PREFIXLEN=0, priority=18000)
            ip.rule('add', fwmark=port, fwmask=0, table=port, priority=20000)
          else:
            ip.route('add', dst=aip, oif=index)
        except Exception as e:
          fatal('could not create route: {}'.format(e))

  if 'post_up' in config['interface']:
    from wgctl.util.exec import run

    info('running post-up commands')

    for cmd in config['interface']['post_up']:
      run(context, cmd)

  ok('tunnel tunnel set up successfully')

@click.command('stop', help='bring down a tunnel')
@click.pass_context
@click.argument('instance')
def down(context, instance):
  instance, config = get_config(instance)

  if not WireGuard().device_exists(ifname=instance):
    fatal('tunnel interface is already down.')

  if 'pre_down' in config['interface']:
    from wgctl.util.exec import run

    info('running pre-down commands')

    for cmd in config['interface']['pre_down']:
      run(context, cmd)

  port = config['interface']['listen_port']

  ip = IPRoute()
  ip.link('delete', ifname=instance)

  nets = [peer.get('allowed_ips', []) for peer in config['peers']]
  nets = [item for sublist in nets for item in sublist]

  if '0.0.0.0/0' in nets:
    try:
      ip.rule('delete', table=254, FRA_SUPPRESS_PREFIXLEN=0, priority=18000)
      ip.rule('delete', fwmark=port, fwmask=0, table=port, priority=20000)
    except:
      pass
  
  ok('tunnel brought down successfully')

@click.command('restart', help='restarts a tunnel (reloading its configuration)')
@click.pass_context
@click.argument('instance')
def downup(context, instance):
  context.invoke(down, instance=instance)
  context.invoke(up, instance=instance)
