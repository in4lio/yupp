# Macros in Python

`yupp` can expand its macro language before CPython parses a direct main
script. This integration is intended for trusted, filesystem-backed scripts
run by CPython 3.11-3.14.

## Install and run

Install the wheel into the same interpreter environment that will open the
script:

```console
python -m pip install yupp
```

Put the source declaration on the first or second line:

```python
#!/usr/bin/env python3
# coding: yupp

($set greeting 'Hello from yupp!')
print(($greeting))
```

Then run the file normally:

```console
python script.py
```

The default base encoding is UTF-8. To decode other source bytes, append a
registered codec name, for example `# coding: yupp.cp1252`.

Site startup installs a small codec-registration hook. When the requested
source bytes match the direct main file, yupp expands the macros, writes the
ordinary generated Python output, and returns that code to CPython. An
unchanged later run may use the generated output cache.

## Supported boundary

The transparent codec supports only the direct filesystem-backed main file.
It intentionally does not preprocess:

- imported modules that declare their own `# coding: yupp` cookie;
- stdin, `python -c`, or zipapps;
- `python -S script.py`, because `-S` disables `site` and `.pth` processing;
- a script run by a different interpreter environment from the one where
  yupp is installed.

A pipx-only installation therefore provides the isolated `yupp` command but
not the codec in an unrelated project's Python interpreter. Install yupp with
that interpreter's `python -m pip` when direct scripts are required.

## Example

The tracked [`glance.yu-py`](../eg/glance/glance.yu-py) template generates
[`glance.py`](../eg/glance/glance.py). It uses Python 3's `configparser`
module and text-mode configuration output:

```python
import time
from configparser import ConfigParser

ini = ConfigParser()
with open('glance.ini', mode='w', encoding='utf8') as stream:
    ini.write(stream)
```

The other Python examples cover source encodings, dictionary-driven output,
coroutines, and generated switch forms. See the [examples index](../eg/README.md).

## Configuration and cache migration

The processor loads directory options from `.yuconfig` and per-source options
from `<source-stem>.yuconfig`. These files are executable Python, not a data
format. Global and per-file configuration share a context, and per-file values
can override directory values. They must use valid Python 3 syntax and APIs.

Python files loaded by `($import ...)` also execute as Python 3. Remove old
`future`, `past`, backport `builtins`, `ConfigParser`, and other Python 2-only
imports when migrating a project.

Caching compares the generated output with its source, loaded configuration,
and declared dependencies. To regenerate after a runtime migration, set
`force = True` in a trusted `.yuconfig` for one run, or update/remove the
generated output, then restore normal cache behavior. A cache hit does not
rewrite the output or create a backup.

## Security

Only preprocess code you trust. The macro evaluator is intentionally not a
sandbox: infix `{ Python }` expressions evaluate Python, imported Python files
execute, and `.yuconfig` executes with yupp's configuration context. Treat all
of these inputs with the same care as ordinary Python source.

## Command-line alternative

Python templates can also use a `.yu-py` suffix and be expanded explicitly:

```console
yupp -q template.yu-py
python template.py
```

This route does not depend on the source codec and is often a better fit for
build systems. `yupp` and `python -m yupp` expose the same CLI and exit status.

[PEP 263](https://peps.python.org/pep-0263/) describes Python source encoding
declarations; yupp uses that mechanism for its registered direct-script codec.
