#!/usr/bin/python3

import os
from setuptools import setup, find_packages


def get_requirements():
    requirements_txt = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'requirements.txt')
    with open(requirements_txt) as fd:
        return fd.read().splitlines()


setup(
    name='jobs',
    version='0.1',
    packages=find_packages(),
    package_data={
        'jobs': [
            'swagger.yaml',
            os.path.join('default_jobs', '*.yaml'),
            os.path.join('default_jobs', '*.yml')
        ]
    },
    scripts=['jobs-api.py'],
    install_requires=get_requirements(),
    include_package_data=True,
    author='Fridolin Pokorny',
    author_email='fridolin@redhat.com',
    maintainer='Fridolin Pokorny',
    maintainer_email='fridolin@redhat.com',
    description='fabric8-analytics Core job service',
    license='ASL 2.0',
    keywords='jobs',
    url='https://github.com/selinon/selinon',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Intended Audience :: Developers",
    ]
)
