from subprocess import Popen, PIPE
from wgctl.util.cli import ok, error, fatal
from sys import exit

def run(context, cmd):
  try:
    cmd = cmd.split(' ')  
    process = Popen(cmd, env={'PATH': ''}, stdout=PIPE, stderr=PIPE)
    _, stderr = process.communicate()

    if process.returncode != 0:
      error('{}'.format(stderr.decode('utf-8').strip()))
      fatal('had to abort early, network stack might be in unknown state.')
  except Exception as e:
    error(e)
    fatal('had to abort early, network stack might be in unknown state.')
