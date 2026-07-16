[![yupp logo](doc/pic/logo.png)](doc/README.md)

# yupp

`yupp` is a lexical macro preprocessor for C, C++, Python, and other text-based
languages. It embeds a small, fully parenthesized macro language into ordinary
source files and emits readable generated text.

`yupp` requires Python 3.11 or newer.

## Install

Install the wheel into the same Python environment that will run `yupp` or a
Python file using the `yupp` source cookie:

```console
python -m pip install yupp
```

For a local checkout:

```console
python -m pip install .
```

`pipx` is useful for isolated command-line applications, but a pipx-only
installation is not suitable for direct `# coding: yupp` scripts: the codec
must be installed in the environment of the Python interpreter that opens the
script.

## Command-line use

Preprocess a source file with either equivalent entry point:

```console
yupp -q eg/hello.yu-c
python -m yupp -q eg/hello.yu-c
```

The suffix determines the output name: for example, `hello.yu-c` produces
`hello.c`, while an ordinary `source.c` produces `source.yugen.c`. Run
`yupp --help` for all configuration and diagnostic options.

```c
($set greeting "Hello ($0)!\n")

#include <stdio.h>

int main(void)
{
    printf(($greeting (`world)));
    return 0;
}
```

Documentation starts with the [language guide](doc/README.md). The
[built-in reference](doc/builtin.md), [Python integration guide](doc/python.md),
[evaluator migration guide](doc/yueval-migration.md), and
[language evolution note](doc/language-evolution.md) cover specialized topics.
Runnable inputs and their checked-in outputs are indexed in
[tracked examples](eg/README.md).

## Direct Python scripts

An installed, site-enabled Python can preprocess a filesystem-backed main
script before Python parses it:

```python
# coding: yupp

($set greeting '!dlrow olleH')
print(($reversed greeting))
```

Run it normally:

```console
python script.py
```

Use `# coding: yupp.cp1252` (or another registered base codec) when the source
bytes are not UTF-8. Unchanged subsequent runs may use the generated output
cache.

The codec contract is deliberately narrow: it supports the direct main file
given to a site-enabled interpreter. Importing a module whose own source uses a
`yupp` cookie is unsupported. So are `python -S`, stdin, `python -c`, zipapps,
and a script run by a different interpreter environment from the one where
`yupp` is installed. In particular, `-S` disables `site` and the `.pth` hook
that registers the codec.

More detail is in [Macros in Python](doc/python.md).

## Security and migration

Process only trusted input. Macro expressions and infix `{ Python }`
expressions can execute Python, `($import ...)` can execute imported Python
files, and `.yuconfig` files are Python scripts. `yupp` is not a sandbox.

The [migration guide](doc/yueval-migration.md) covers Python 3 project updates,
cache regeneration, evaluator scope and conditional changes, the optional
dynamic-scope warning, and the full compatibility table.

## Development

Run the local suite and build both distribution formats with:

```console
python -m pip install pytest build twine
python -m pytest -q
python -m build
python -m twine check --strict dist/*
```

The wheel is the installation artifact used by clean-environment tests. The
repository keeps generated examples next to their source templates; update a
template first, regenerate with the current engine, and review both diffs.

The bundled [Sublime Text files](sublime_text/README.md) remain a manually
installed editor integration.

The repository has one public documentation tree:

- `src/yupp/` contains the installable package and bundled macro libraries;
- `tests/` contains unit, integration, packaging, and compatibility tests;
- `eg/` contains source templates and their deterministic generated outputs;
- `doc/` contains the language documentation and its images;
- `script/` contains developer utilities such as the evaluator benchmark;
- `sublime_text/` contains the optional, manually installed editor integration.

Build products, caches, virtual environments, and editor-local settings are
ignored and must not be committed.

## License

See [LICENSE](LICENSE).
