#!/bin/bash

set -o errexit
set -o nounset

python3 -m celery -A main.app worker --loglevel=info