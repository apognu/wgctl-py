from subprocess import Popen, PIPE
from wgctl.util.cli import ok, error, fatal
from sys import exit

def run(context, cmd, label=None, split=True, abort_on_error=True, silence=False, show_output=False, return_output=False):
  verbose = context.obj['verbose']

  if split:
    cmd = cmd.split(' ')
  if label is None:
    label = ' '.join(cmd)
  
  process = Popen(cmd, stdout=PIPE, stderr=PIPE)
  stdout, stderr = process.communicate()

  if show_output:
    print(stdout.decode('utf-8'))
  
  if process.returncode != 0 and abort_on_error:
    if not silence and verbose:
      print('[✗] {} ({})'.format(label, stderr.decode('utf-8').strip()))
    
    print('ERROR: had to abort early, network stack might be in unknown state.')
    exit(1)

  if not silence and verbose:
    print('[✓] {}'.format(label))
  
  if return_output:
    return (process.returncode == 0, stdout.decode('utf-8'))

  return process.returncode == 0