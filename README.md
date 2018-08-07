# wgctl - WireGuard control utility

This is a personal project to allow WireGuard to be configured through the use of YAML files. It uses Netlink under the hood for all interaction with the system.

This tool is very opinionated and designed for my own use, it _might_ not be what you're looking for. For instance, it probably does not handle IPv6 very well for now.

The configuration file should look like this:

```
description: Personal VPN server #1
interface:
  address: 192.168.0.1/32
  listen_port: 42000
  private_key: /etc/wireguard/vpn1.key
peers:
  - description: VPN gateway at provider X
    public_key: cyfBMbaJ6kgnDYjio6xqWikvTz2HvpmvSQocRmF/ZD4=
    endpoint: 1.2.3.4:42000
    allowed_ips:
      - 192.168.0.0/24
      - 192.168.1.0/24
```

By default, ```wgctl``` will look for its configuration files under ```/etc/wireguard``` (as ```/etc/wireguard/<id>.yml```). This can be overriden by giving it a filesystem path instead of an identifier.

## Usage

```
$ wgctl --help
Usage: wgctl [OPTIONS] COMMAND [ARGS]...

Options:
  -v, --verbose
  --help         Show this message and exit.

Commands:
  down     bring down a tunnel
  downup   restarts a tunnel (reloading its...
  info     shows information on a particular tunnel
  status   shows if a tunnel is up
  up       starts up a tunnel
  version

$ wgctl up vpn1
[✓] WireGuard tunnel set up successfully

$ wgctl up vpn2
[✓] WireGuard tunnel set up successfully

$ wgctl status
[✓] Personal VPN server #1 (vpn1)
[✓] Personal VPN server #2 (vpn2)

$ wgctl downup vpn1
[✓] WireGuard tunnel brought down successfully
[✓] WireGuard tunnel set up successfully

$ wgctl info vpn1
tunnel: Personal VPN server #1
  interface: vpn1
  public key: 7cm1E7OnH3GV7p5CatWYHbw7NJX2ljzDaRMTYWWgLk0=
  listening port: 42000

  - peer: VPN gateway at provider X
    public key: cyfBMbaJ6kgnDYjio6xqWikvTz2HvpmvSQocRmF/ZD4=
    endpoint: 1.2.3.4:42000
    allowed ips: 192.168.0.0/24, 192.168.1.0/24
    preshared key? True
```