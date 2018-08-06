from setuptools import setup, find_packages

setup(
  name='wgctl',
  version='0.1',
  packages=find_packages(),
  include_package_data=True,
  install_requires=[
    'Click',
    'pyyaml'
  ],
  entry_points='''
    [console_scripts]
    wgctl=wgctl.main:main
  ''',
)
