#!/bin/sh

cd "$(dirname $0)/../package"

python3 -m twine upload --repository pypi dist/*
