#!/usr/bin/env bash
set -ex

# Let's use the latest version during development
yum install -y git
pip3 install -U git+https://github.com/selinon/selinonlib
pip3 install -U git+https://github.com/selinon/selinon
