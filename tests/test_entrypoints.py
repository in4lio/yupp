import os
import subprocess
import sys

import pytest

from tests.conftest import REPO_ROOT


def run_without_site_packages(code):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(REPO_ROOT / "src")
    return subprocess.run(
        [sys.executable, "-S", "-c", code],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def test_import_yupp_is_stdlib_only_and_has_no_runtime_side_effects():
    process = run_without_site_packages(
        "import logging, sys\n"
        "recursion_limit = sys.getrecursionlimit()\n"
        "handler_counts = {name: len(logging.getLogger(name).handlers) "
        "for name in ('log', 'trace')}\n"
        "import yupp\n"
        "assert 'yupp.pp.yugen' not in sys.modules\n"
        "assert sys.getrecursionlimit() == recursion_limit\n"
        "assert {name: len(logging.getLogger(name).handlers) "
        "for name in ('log', 'trace')} == handler_counts\n"
        "assert yupp.__version__ == '2.0rc1'\n"
    )

    assert process.returncode == 0, process.stderr


def test_startup_loader_replaces_namespace_style_existing_module():
    loader = REPO_ROOT / "src" / "yupp" / "_site.py"
    process = run_without_site_packages(
        "import codecs, importlib.util, pathlib, sys, types\n"
        "existing = types.ModuleType('yupp')\n"
        "existing.__file__ = None\n"
        "existing.sentinel = object()\n"
        "sys.modules['yupp'] = existing\n"
        f"loader = pathlib.Path({str(loader)!r})\n"
        "spec = importlib.util.spec_from_file_location('__yupp_site__', loader)\n"
        "startup = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(startup)\n"
        "loaded = sys.modules['yupp']\n"
        "assert loaded is not existing\n"
        "assert pathlib.Path(loaded.__file__).samefile(loader.with_name('__init__.py'))\n"
        "assert not hasattr(loaded, 'sentinel')\n"
        "assert codecs.lookup('yupp').name == 'yupp'\n"
    )

    assert process.returncode == 0, process.stderr


def test_public_api_is_lazy_and_codec_registration_is_idempotent():
    process = run_without_site_packages(
        "import codecs, importlib, sys\n"
        "registrations = []\n"
        "original_register = codecs.register\n"
        "def register(search_function):\n"
        "    registrations.append(search_function)\n"
        "    return original_register(search_function)\n"
        "codecs.register = register\n"
        "import yupp\n"
        "assert 'yupp.pp.yugen' not in sys.modules\n"
        "importlib.reload(yupp)\n"
        "assert len(registrations) == 1\n"
        "assert callable(yupp.cli)\n"
        "assert callable(yupp.translate)\n"
        "assert 'yupp.pp.yugen' in sys.modules\n"
    )

    assert process.returncode == 0, process.stderr


@pytest.mark.parametrize("module", ["yupp", "yupp.pp"])
def test_module_entrypoint_propagates_cli_failure_status(tmp_path, module):
    source = tmp_path / "broken.yu-c"
    source.write_text("($set missing", encoding="utf8")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(REPO_ROOT / "src")

    process = subprocess.run(
        [
            sys.executable,
            "-S",
            "-m",
            module,
            "-q",
            "--no-read-only",
            str(source),
        ],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert process.returncode == 4
    assert not (tmp_path / "broken.c").exists()


def test_module_entrypoints_keep_zero_two_and_four_per_failure_statuses(tmp_path):
    good = tmp_path / "good.yu-c"
    good.write_text("OK\n", encoding="utf8")
    bad_one = tmp_path / "bad-one.yu-c"
    bad_one.write_text("($set missing", encoding="utf8")
    bad_two = tmp_path / "bad-two.yu-c"
    bad_two.write_text("($set also-missing", encoding="utf8")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(REPO_ROOT / "src")

    def run(module, *arguments):
        return subprocess.run(
            [sys.executable, "-S", "-m", module, *arguments],
            cwd=tmp_path,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )

    for module in ("yupp", "yupp.pp"):
        success = run(module, "-q", "--no-read-only", str(good))
        usage = run(module, "--definitely-not-an-option")
        failures = run(
            module,
            "-q",
            "--no-read-only",
            str(bad_one),
            str(bad_two),
        )

        assert success.returncode == 0, success.stderr
        assert usage.returncode == 2
        assert failures.returncode == 8


@pytest.mark.parametrize("module_name", ["yupp.__main__", "yupp.pp.__main__"])
def test_module_entrypoint_propagates_program_execution_status_one(
    module_name, monkeypatch
):
    module = __import__(module_name, fromlist=["main"])
    monkeypatch.setattr(module, "cli", lambda arguments: 1)
    monkeypatch.setattr(sys, "argv", [module_name])

    assert module.main() == 1
