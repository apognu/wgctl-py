# Module adapted from artizirk's work
# Original source: https://gist.github.com/artizirk/3a8efeee33fce34baf6047aed7205a2e

import struct
import socket
from socket import AF_INET, AF_INET6
from socket import inet_pton, inet_ntop

import datetime
from base64 import b64encode, b64decode

from pyroute2.netlink import NLM_F_REQUEST, NLM_F_DUMP, NLM_F_ACK
from pyroute2.netlink import nla, nla_base
from pyroute2.netlink import genlmsg
from pyroute2.netlink.generic import GenericNetlinkSocket

from wgctl.util.network import parse_key, parse_net
from wgctl.util.cli import fatal
from pyroute2 import IPRoute

WG_GENL_NAME = 'wireguard'
WG_GENL_VERSION = 1

WG_KEY_LEN = 32

WG_CMD_GET_DEVICE = 0
WG_CMD_SET_DEVICE = 1

class wgmsg(genlmsg):
  prefix = 'WGDEVICE_A_'
  nla_map = (
    ('WGDEVICE_A_UNSPEC', 'none'),
    ('WGDEVICE_A_IFINDEX', 'uint32'),
    ('WGDEVICE_A_IFNAME', 'asciiz'),
    ('WGDEVICE_A_PRIVATE_KEY', 'cdata'),
    ('WGDEVICE_A_PUBLIC_KEY', 'cdata'),
    ('WGDEVICE_A_FLAGS', 'uint32'),
    ('WGDEVICE_A_LISTEN_PORT', 'uint16'),
    ('WGDEVICE_A_FWMARK', 'uint32'),
    ('WGDEVICE_A_PEERS', '*wgpeer')
  )

  class wgpeer(nla):
    prefix = 'WGPEER_A_'
    nla_map = (
      ('WGPEER_A_UNSPEC', 'none'),
      ('WGPEER_A_PUBLIC_KEY', 'cdata'),
      ('WGPEER_A_PRESHARED_KEY', 'cdata'),
      ('WGPEER_A_FLAGS', 'uint32'),
      ('WGPEER_A_ENDPOINT', 'sockaddr'),
      ('WGPEER_A_PERSISTENT_KEEPALIVE_INTERVAL', 'uint16'),
      ('WGPEER_A_LAST_HANDSHAKE_TIME', 'timespec'),
      ('WGPEER_A_RX_BYTES', 'uint64'),
      ('WGPEER_A_TX_BYTES', 'uint64'),
      ('WGPEER_A_ALLOWEDIPS', '*wgallowedip')
    )

    class sockaddr(nla_base):
      """
      # IPv4
      struct sockaddr_in {
         uint16_t    sin_family; /* address family: AF_INET */
         uint16_t    sin_port;   /* port in network byte order */
         uint32_t    sin_addr;   /* internet address */
      };

      # IPv6
      struct sockaddr_in6 {
         uint16_t    sin6_family;   /* AF_INET6 */
         uint16_t    sin6_port;   /* port number */
         uint32_t    sin6_flowinfo; /* IPv6 flow information */
         uint8_t     sin6_addr[16]; /* IPv6 address */
         uint32_t    sin6_scope_id; /* Scope ID (new in 2.4) */
      };
      """

      fields = [('value', 's')]

      def encode(self):
        nla_base.encode(self)

      def decode(self):
        nla_base.decode(self)
        family = struct.unpack('H', self['value'][:2])[0]
        if family == AF_INET:
          port, host = struct.unpack('!H4s', self['value'][2:8])
          self.value = (inet_ntop(family, host), port)
        elif family == AF_INET6:
          port, flowinfo, host, scopeid = struct.unpack('!HI16sI', self['value'][2:28])
          self.value = (inet_ntop(family, host), port, flowinfo, scopeid)

    class timespec(nla):
      fields = [('value', 's')]

      def decode(self):
        nla_base.decode(self)
        sec, _ = struct.unpack('ll', self['value'])
        self.value = datetime.datetime.fromtimestamp(sec)

    class wgallowedip(nla):
      prefix = 'WGALLOWEDIP_A_'
      nla_map = (
        ('WGALLOWEDIP_A_UNSPEC', 'none'),
        ('WGALLOWEDIP_A_FAMILY', 'uint16'),
        ('WGALLOWEDIP_A_IPADDR', 'ipaddr'),
        ('WGALLOWEDIP_A_CIDR_MASK', 'uint8')
      )

class WireGuard(GenericNetlinkSocket):
  def __init__(self, *args, **kwargs):
    GenericNetlinkSocket.__init__(self, *args, **kwargs)
    GenericNetlinkSocket.bind(self, WG_GENL_NAME, wgmsg, *args, **kwargs)

  def get_devices(self):
    ip = IPRoute()
    links = [link.get_attr('IFLA_IFNAME') for link in ip.get_links() if self.device_exists(link.get_attr('IFLA_IFNAME'))]

    return links

  def device_exists(self, ifname=None, ifindex=None):
    """
    Returns True if the given device exists and is a WireGuard device
    """

    try:
      msg = wgmsg()
      msg['cmd'] = WG_CMD_GET_DEVICE
      msg['version'] = WG_GENL_VERSION
      
      if ifname != None:
        msg['attrs'].append(['WGDEVICE_A_IFNAME', ifname])
      elif ifindex != None:
        msg['attrs'].append(['WGDEVICE_A_IFINDEX', ifindex])
      else:
        raise ValueError("ifname or ifindex are unset")
      
      self.nlm_request(msg, msg_type=self.prid, msg_flags=NLM_F_REQUEST | NLM_F_ACK | NLM_F_DUMP)

      return True
    except:
      return False

  def get_device_dump(self, ifname=None, ifindex=None):
    """
    Return current configuration of wireguard device
    by name or by interface index
    """

    msg = wgmsg()
    msg['cmd'] = WG_CMD_GET_DEVICE
    msg['version'] = WG_GENL_VERSION
    if ifname != None:
      msg['attrs'].append(['WGDEVICE_A_IFNAME', ifname])
    elif ifindex != None:
      msg['attrs'].append(['WGDEVICE_A_IFINDEX', ifindex])
    else:
      raise ValueError("ifname or ifindex are unset")
    return self.nlm_request(msg, msg_type=self.prid, msg_flags=NLM_F_REQUEST | NLM_F_ACK | NLM_F_DUMP)

  def get_device_dict(self, *args, **kwargs):
    msg = self.get_device_dump(*args, **kwargs)
    ret = {}
    for x in msg:
      dev = ret[x.get_attr('WGDEVICE_A_IFNAME')] = {}
      for key, val in x['attrs']:
        key = key.replace(x.prefix, '', 1).lower()
        if key == 'peers':
          peers = []
          for peer in val:
            p = {}
            peers.append(p)
            for peer_key, peer_val in peer['attrs']:
              peer_key = peer_key.replace(peer.prefix, '', 1).lower()
              if peer_key == 'allowedips':
                allowedips = []
                for ips in peer_val:
                  ip = ips.get_attr('WGALLOWEDIP_A_IPADDR')
                  mask = ips.get_attr('WGALLOWEDIP_A_CIDR_MASK')
                  allowedips.append('{}/{}'.format(ip, mask))
                peer_val = allowedips
              p[peer_key] = peer_val
          val = peers
        dev[key] = val
    return ret

  def set_device(self, ifname=None, ifindex=None, config={}):
    msg = wgmsg()
    msg['cmd'] = WG_CMD_SET_DEVICE
    msg['version'] = WG_GENL_VERSION

    if ifname != None:
      msg['attrs'].append(['WGDEVICE_A_IFNAME', ifname])
    elif ifindex != None:
      msg['attrs'].append(['WGDEVICE_A_IFINDEX', ifindex])
    else:
      raise ValueError('ifname or ifindex are unset')

    interface = config.get('interface')
    if interface is None:
      fatal('configuration is missing "interface" key')
    
    port = interface.get('listen_port')
    pkey = interface.get('private_key')
    if not all([port, pkey]):
      fatal('interface must have at least a "private_key" and "listen_port"')

    fwmark = interface.get('fwmark')
    peers = config.get('peers')

    if port != None:
      msg['attrs'].append(['WGDEVICE_A_LISTEN_PORT', port])
    if fwmark != None:
      msg['attrs'].append(['WGDEVICE_A_FWMARK', fwmark])
    if pkey != None:
      msg['attrs'].append(['WGDEVICE_A_PRIVATE_KEY', parse_key('private_key', pkey)])
    
    if peers is not None:
      wgpeers = []
      
      for peer in peers:
        wgpeer = wgmsg.wgpeer()

        if 'preshared_key' in peer:
          if len(peer['preshared_key']) != 64:
            fatal('pre-shared key must be 64 hexadecimal characters')
          
          wgpeer['attrs'].append(['WGPEER_A_PRESHARED_KEY', bytearray.fromhex(peer['preshared_key'])])

        if 'persistent_keepalive_interval' in peer:
          try:
            wgpeer['attrs'].append(['WGPEER_A_PERSISTENT_KEEPALIVE_INTERVAL', int(peer['persistent_keepalive_interval'])])
          except ValueError:
            pass

        if 'endpoint' in peer:
          try:
            host, port = peer['endpoint'].rsplit(':')
            port = int(port)
            address = \
              struct.pack('H', socket.AF_INET) + \
              struct.pack('!H12s', port, socket.inet_aton(host))

            addr = wgmsg.wgpeer.sockaddr()
            addr.setvalue(address)

            wgpeer['attrs'].append(['WGPEER_A_ENDPOINT', addr])
          except ValueError:
            raise ValueError('peer endpoint is malformed')
        
        if 'public_key' in peer:
          wgpeer['attrs'].append(['WGPEER_A_PUBLIC_KEY', parse_key('public_key', peer['public_key'])])

        if 'allowed_ips' in peer:
          wgips = []
          
          for ip in peer['allowed_ips']:
            net, cidr = ip.rsplit('/')
            cidr = int(cidr)

            wgip = wgmsg.wgpeer.wgallowedip()
            wgip['attrs'].append(['WGALLOWEDIP_A_FAMILY', AF_INET])
            wgip['attrs'].append(['WGALLOWEDIP_A_IPADDR', net])
            wgip['attrs'].append(['WGALLOWEDIP_A_CIDR_MASK', cidr])

            wgips.append(wgip)
          
          wgpeer['attrs'].append(['WGPEER_A_ALLOWEDIPS', wgips])

        wgpeers.append(wgpeer)
      
      msg['attrs'].append(['WGDEVICE_A_PEERS', wgpeers])

    return self.put(msg, msg_type=self.prid, msg_flags=NLM_F_REQUEST)
