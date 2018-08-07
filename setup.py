from setuptools import setup, find_packages

setup(
  name='wgctl',
  version='0.1.0',
  author='Antoine POPINEAU',
  author_email='antoine.popineau@gmail.com',
  packages=find_packages(),
  include_package_data=True,
  install_requires=[
    'Click',
    'pyyaml',
    'pyroute2',
    'colorama'
  ],
  entry_points='''
    [console_scripts]
    wgctl=wgctl.main:main
  ''',
  classifiers=(
    'Programming Language :: Python :: 3',
    'Licence :: OSI Approved :: MIT Licence',
    'Operating System :: Linux'
  )
)
