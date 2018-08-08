import yaml

from os import path
from pathlib import Path
from wgctl.util.cli import fatal

def get_config(instance):
  config_path = '/etc/wireguard/{}.yml'.format(instance)
  if path.isfile(instance):
    config_path = instance
    instance = Path(instance).resolve().stem
  
  try:
    with open(config_path) as stream:
      config = yaml.load(stream)
  except FileNotFoundError:
    fatal('could not read file: {}'.format(config_path))
  except yaml.YAMLError:
    fatal('could not parse configuration')

  check_config(config)

  return instance, config

def check_config(config):
  if config is None:
    fail()
  
  if type(config.get('interface')) is not dict:
    fail('there must be an interface definition')
  if config['interface'].get('private_key') is None:
    fail('the interface must have a private key')
  if type(config['interface'].get('listen_port')) is not int:
    fail('the interface must have an integer listening port')
  
  if type(config.get('peers', [])) is not list:
    fail('the peers definition must be a list')

def fail(message=None):
  if message is None:
    fatal('could not parse configuration')
  else:
    fatal('could not parse configuration: {}'.format(message))
