#!/bin/sh

cd "$(dirname $0)/../package"

python -m pip uninstall -y yupp
python setup.py sdist upload
