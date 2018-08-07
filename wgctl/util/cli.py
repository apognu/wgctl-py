from sys import exit
from colorama import Fore, Style

def fatal(message):
  print('{}{}[✗]{} ERROR: {}'.format(Style.BRIGHT, Fore.RED, Fore.RESET, message))
  exit(1)

def info(message):
  print('{}[-]{} {}'.format(Style.BRIGHT, Style.RESET_ALL, message))

def ok(message, symbol='✓'):
  print('{}[{}]{} {}'.format(Fore.GREEN, symbol, Style.RESET_ALL, message))

def dim(message, symbol='-'):
  print('{}[{}] {}'.format(Style.DIM, symbol, message))

def error(message, details=None):
  if details is None:
    print('{}{}[✗]{} {}'.format(Style.BRIGHT, Fore.RED, Fore.RESET, message))
  else:
    print('{}{}[✗]{} {} ({})'.format(Style.BRIGHT, Fore.RED, Fore.RESET, message, details))