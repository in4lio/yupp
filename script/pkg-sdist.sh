#!/bin/sh

cd "$(dirname $0)/../package"

python -m pip uninstall -y yupp
python3 -m pip uninstall -y yupp
python3 setup.py sdist
