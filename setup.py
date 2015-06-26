# coding:utf-8

import sys
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.version_info < (2, 6):
    error = 'ERROR: qingcloud-sdk requires Python Version 2.6 or above.'
    print >> sys.stderr, error
    sys.exit(1)


setup(
    name = 'qingcloud-openstack',
    version = '0.1.0',
    description = 'QingCloud API for Openstack.',
    long_description = open('README.rst', 'rb').read().decode('utf-8'),
    keywords = 'qingcloud for openstack api',
    author = 'Yunify Team',
    author_email = 'vincent@yunify.com',
    url = 'https://www.qingcloud.com',
    packages = ['qingcloud', 'qingcloud.conn', 'qingcloud.iaas', 'qingcloud.misc'],
    package_dir = {'qingcloud-sdk': 'qingcloud'},
    namespace_packages = ['qingcloud'],
    include_package_data = True,
    install_requires = [
        'PyYAML>=3.1',
    ]
)
