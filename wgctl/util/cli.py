from sys import exit

def fatal(message):
  print('ERROR: {}'.format(message))
  exit(1)

def info(message):
  print('[-] {}'.format(message))

def ok(message):
  print('[✓] {}'.format(message))

def error(message, details=None):
  if details is None:
    print('[✗] {}'.format(message))
  else:
    print('[✗] {} ({})'.format(message, details))