#!/bin/sh

cd "$(dirname $0)/.."

# ---- pp ----

cp -fv ./README ./package/
cp -fv ./LICENSE ./package/

mkdir -p ./package/yupp/
cp -fv ./__main__.py ./package/yupp/
cp -fv ./__init__.py ./package/yupp/

mkdir -p ./package/yupp/pp/
cp -fv ./pp/__init__.py ./package/yupp/pp/
cp -fv ./pp/yup.py ./package/yupp/pp/
cp -fv ./pp/yugen.py ./package/yupp/pp/
cp -fv ./pp/yuconfig.py ./package/yupp/pp/
cp -fv ./pp/yulic.py ./package/yupp/pp/

mkdir -p ./package/yupp/pylib
cp -fv ./pylib/__init__.py ./package/yupp/pylib/
cp -fv ./pylib/yutraceback.py ./package/yupp/pylib/
cp -fv ./pylib/yutraceback2.py ./package/yupp/pylib/
cp -fv ./pylib/yutraceback3.py ./package/yupp/pylib/

# ---- lib ----

mkdir -p ./package/yupp/lib/
cp -fv ./lib/corolib.yu ./package/yupp/lib/
cp -fv ./lib/coroutine-h.yu ./package/yupp/lib/
cp -fv ./lib/coroutine-py.yu ./package/yupp/lib/
cp -fv ./lib/coroutine.h ./package/yupp/lib/
cp -fv ./lib/coroutine.yu ./package/yupp/lib/
cp -fv ./lib/h-light.yu ./package/yupp/lib/
cp -fv ./lib/h.yu ./package/yupp/lib/
cp -fv ./lib/hlib.yu ./package/yupp/lib/
cp -fv ./lib/stdlib.yu ./package/yupp/lib/
