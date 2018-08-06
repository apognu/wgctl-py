import click

from wgctl.util.exec import run
from wgctl.util.cli import ok, fatal, info
from wgctl.util.config import get_config

@click.command(help='starts up a tunnel')
@click.pass_context
@click.argument('instance')
def up(context, instance):
  verbose = context.obj['verbose']
  instance, config = get_config(instance)

  if run(context, 'wg show {}'.format(instance), abort_on_error=False, silence=True):
    fatal('WireGuard interface is already up.')

  address = config['interface']['address']
  port = str(config['interface']['listen_port'])
  pkey = config['interface']['private_key']

  run(context, 'ip link add {} type wireguard'.format(instance), label='Creating interface {}'.format(instance))
  run(context, 'ip address add {} dev {}'.format(address, instance), label='Setting IP address {}'.format(address))
  run(context, 'ip link set {} up'.format(instance), label='Enabling interface')
  
  wg_args = [
    'wg', 'set', instance,
    'listen-port', port,
    'private-key', pkey,
  ]

  for peer in config['peers']:
    wg_args = wg_args + ['peer', peer['public_key']]

    if peer['endpoint']:
      wg_args = wg_args + ['endpoint', peer['endpoint']]
    if peer['allowed_ips']:
      wg_args = wg_args + ['allowed-ips', ','.join(peer['allowed_ips'])]
    
    for net in peer['allowed_ips']:
      if net == '0.0.0.0/0':
        if verbose:
          info('Catch-all subnet detected, setting default route')

        run(context, 'wg set {} fwmark {}'.format(instance, port), label=' -> Setting fwmark {}'.format(port))
        run(context, 'ip route add default dev {} table {}'.format(instance, port), label=' -> Adding default route to table {}'.format(port))
        run(context, 'ip rule add not fwmark {0} table {0}'.format(port), label=' -> Adding a rule for all traffic to table {}'.format(port))
        run(context, 'ip rule add table main suppress_prefixlength 0 priority 32000', label=' -> Addding suppress_prefixlength to main routing table')
      else:
        run(context, 'ip route add {} dev {}'.format(net, instance))
  
  run(context, wg_args, split=False, label='Setting up WireGuard parameters')

  ok('WireGuard tunnel set up successfully')

@click.command(help='bring down a tunnel')
@click.pass_context
@click.argument('instance')
def down(context, instance):
  instance, config = get_config(instance)

  if not run(context, 'wg show {}'.format(instance), abort_on_error=False, silence=True):
    fatal('WireGuard interface is already down.')

  port = str(config['interface']['listen_port'])
  
  run(context, 'ip link delete {}'.format(instance), abort_on_error=False, label='Deleting interface {}'.format(instance))
  run(context, 'ip rule delete not from all fwmark {0} lookup {0}'.format(port), abort_on_error=False)
  run(context, 'ip rule delete table main priority 32000', label=' -> Deleting suppress_prefixlength to main routing table', abort_on_error=False)

  ok('WireGuard tunnel brought down successfully')

@click.command(help='restarts a tunnel (reloading its configuration)')
@click.pass_context
@click.argument('instance')
def downup(context, instance):
  context.invoke(down, instance=instance)
  context.invoke(up, instance=instance)