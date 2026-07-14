import os
import subprocess
import sys

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
        "assert yupp.__version__ == '1.2c1'\n"
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


def test_module_entrypoint_propagates_cli_failure_status(tmp_path):
    source = tmp_path / "broken.yu-c"
    source.write_text("($set missing", encoding="utf8")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(REPO_ROOT / "src")

    process = subprocess.run(
        [
            sys.executable,
            "-S",
            "-m",
            "yupp",
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
