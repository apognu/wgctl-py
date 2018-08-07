import wgctl

from base64 import b64encode, b64decode

def parse_key(kind, key):
  key = b64decode(key)

  if type(key) != bytes:
    raise ValueError('{} has to be bytes'.format(kind))
  elif len(key) != wgctl.util.netlink.WG_KEY_LEN:
    raise ValueError('{} length has to be {}'.format(kind, wgctl.util.netlink.WG_KEY_LEN))
  
  return key

def format_key(key):
  return b64encode(key).decode()

def parse_net(net):
  net, cidr = net.rsplit('/')
  cidr = int(cidr)

  return net, cidr