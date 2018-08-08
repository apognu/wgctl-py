from setuptools import setup, find_packages

with open('README.md', 'r') as rm:
  long_description = rm.read()

setup(
  name='wgctl',
  version='0.1.0',
  author='Antoine POPINEAU',
  author_email='antoine.popineau@gmail.com',
  description='Manage your WireGuard tunnels easily',
  long_description=long_description,
  long_description_content_type='text/markdown',
  url='https://github.com/apognu/wgctl',
  packages=find_packages(),
  include_package_data=True,
  install_requires=[
    'Click',
    'pyyaml',
    'pyroute2',
    'timeago',
    'colorama'
  ],
  entry_points='''
    [console_scripts]
    wgctl=wgctl.main:main
  ''',
  classifiers=(
    'Programming Language :: Python :: 3',
    'License :: OSI Approved :: MIT License',
    'Operating System :: POSIX :: Linux'
  )
)
