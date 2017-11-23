#!/usr/bin/env bash

set -ex

jobs-api.py initjobs
cd /usr/bin/
exec uwsgi --http 0.0.0.0:30000 -p 1 -w jobs-api --enable-threads
