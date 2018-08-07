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
  
  return instance, config