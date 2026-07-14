"""Path-anchored interpreter-startup bootstrap for the yupp source codec.

This file is executed by the adjacent ``yupp.pth``.  It deliberately loads
the package from the directory containing this file instead of resolving
``import yupp`` through ``sys.path``: a ``yupp.py`` in the working directory
must never run merely because the interpreter processed the installed hook.
"""

import importlib.util
import os
import sys


def _same_file(left, right):
    try:
        return os.path.samefile(left, right)
    except (OSError, TypeError, ValueError):
        return os.path.abspath(os.fspath(left)) == os.path.abspath(os.fspath(right))


def _load_installed_package():
    package_dir = os.path.dirname(os.path.abspath(__file__))
    package_init = os.path.join(package_dir, "__init__.py")
    existing = sys.modules.get("yupp")
    if existing is not None and _same_file(
        getattr(existing, "__file__", ""), package_init
    ):
        return existing

    spec = importlib.util.spec_from_file_location(
        "yupp", package_init, submodule_search_locations=[package_dir]
    )
    if spec is None or spec.loader is None:
        raise ImportError("cannot create the installed yupp package spec")
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get("yupp")
    sys.modules["yupp"] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        if previous is None:
            sys.modules.pop("yupp", None)
        else:
            sys.modules["yupp"] = previous
        raise
    return module


_load_installed_package()
