import ast
import base64
import csv
import email.parser
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import zipfile

import pytest

from tests.conftest import REPO_ROOT


def _clean_environment():
    environment = os.environ.copy()
    for name in (
        "PYTHONHOME",
        "PYTHONPATH",
        "PYTHONSTARTUP",
        "PYTHONUSERBASE",
    ):
        environment.pop(name, None)
    environment["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    environment["PYTHONNOUSERSITE"] = "1"
    return environment


def _run(arguments, *, cwd, environment=None):
    process = subprocess.run(
        [str(argument) for argument in arguments],
        cwd=cwd,
        env=environment or _clean_environment(),
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert process.returncode == 0, (
        f"command failed ({process.returncode}): {' '.join(map(str, arguments))}\n"
        f"stdout:\n{process.stdout}\nstderr:\n{process.stderr}"
    )
    return process


def _python_in(venv):
    directory = "Scripts" if os.name == "nt" else "bin"
    executable = "python.exe" if os.name == "nt" else "python"
    return venv / directory / executable


def _console_in(venv):
    directory = "Scripts" if os.name == "nt" else "bin"
    executable = "yupp.exe" if os.name == "nt" else "yupp"
    return venv / directory / executable


@pytest.fixture(scope="session")
def distributions(tmp_path_factory):
    supplied = os.environ.get("YUPP_DISTRIBUTIONS")
    if supplied:
        output = Path(supplied).resolve()
        assert output.is_dir(), f"YUPP_DISTRIBUTIONS is not a directory: {output}"
        wheels = tuple(output.glob("*.whl"))
        sdists = tuple(output.glob("*.tar.gz"))
        assert len(wheels) == 1, f"expected one wheel in {output}, found {wheels}"
        assert len(sdists) == 1, f"expected one sdist in {output}, found {sdists}"
        return wheels[0], sdists[0]

    output = tmp_path_factory.mktemp("distributions")
    _run(
        [sys.executable, "-m", "build", "--no-isolation", "--outdir", output, REPO_ROOT],
        cwd=output,
    )
    wheels = tuple(output.glob("*.whl"))
    sdists = tuple(output.glob("*.tar.gz"))
    assert len(wheels) == 1
    assert len(sdists) == 1
    return wheels[0], sdists[0]


def _wheel_payload(wheel):
    with zipfile.ZipFile(wheel) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def _assert_wheel_record(payload):
    record_name = next(name for name in payload if name.endswith(".dist-info/RECORD"))
    record = list(csv.reader(payload[record_name].decode("utf8").splitlines()))
    recorded_names = [row[0] for row in record]
    assert set(recorded_names) == set(payload)

    for name, digest, size in record:
        if name == record_name:
            assert digest == ""
            assert size == ""
            continue
        expected = base64.urlsafe_b64encode(
            hashlib.sha256(payload[name]).digest()
        ).rstrip(b"=").decode("ascii")
        assert digest == f"sha256={expected}"
        assert size == str(len(payload[name]))
    return recorded_names


def _normalized_wheel_payload(wheel):
    payload = _wheel_payload(wheel)
    _assert_wheel_record(payload)
    wheel_name = next(name for name in payload if name.endswith(".dist-info/WHEEL"))
    record_name = next(name for name in payload if name.endswith(".dist-info/RECORD"))
    payload[wheel_name] = b"\n".join(
        b"Generator: <normalized>" if line.startswith(b"Generator: ") else line
        for line in payload[wheel_name].split(b"\n")
    )
    del payload[record_name]
    return payload


@pytest.mark.packaging
def test_metadata_is_static_and_artifacts_are_complete(distributions):
    wheel, sdist = distributions
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf8")
    setup_source = (REPO_ROOT / "setup.py").read_text(encoding="utf8")
    setup_tree = ast.parse(setup_source)

    assert "requires-python = \">=3.11\"" in pyproject
    assert "dependencies = []" in pyproject
    assert "dynamic =" not in pyproject
    assert not any(
        isinstance(node, (ast.Import, ast.ImportFrom))
        and any(alias.name == "yupp" or alias.name.startswith("yupp.") for alias in node.names)
        for node in ast.walk(setup_tree)
    )

    payload = _wheel_payload(wheel)
    names = tuple(payload)
    dist_info = next(name.split("/", 1)[0] for name in names if name.endswith("/METADATA"))
    metadata = email.parser.BytesParser().parsebytes(payload[f"{dist_info}/METADATA"])
    assert metadata["Name"] == "yupp"
    assert metadata["Version"] == "1.2rc1"
    assert metadata["Requires-Python"] == ">=3.11"
    assert metadata.get_all("Requires-Dist") is None
    assert b"yupp = yupp.__main__:main" in payload[f"{dist_info}/entry_points.txt"]
    assert b"Root-Is-Purelib: true" in payload[f"{dist_info}/WHEEL"]
    assert b"Tag: py3-none-any" in payload[f"{dist_info}/WHEEL"]

    assert names.count("yupp.pth") == 1
    recorded_names = _assert_wheel_record(payload)
    assert recorded_names.count("yupp.pth") == 1
    assert set(recorded_names) == set(names)

    required_resources = {
        "yupp/lib/README.md",
        "yupp/lib/corolib.yu",
        "yupp/lib/coroutine-h.yu",
        "yupp/lib/coroutine-py.yu",
        "yupp/lib/coroutine.h",
        "yupp/lib/coroutine.yu",
        "yupp/lib/h-light.yu",
        "yupp/lib/h.yu",
        "yupp/lib/hlib.yu",
        "yupp/lib/stdlib.yu",
        "yupp/lib/eg/lib.py",
    }
    assert required_resources <= set(names)

    with tarfile.open(sdist, "r:gz") as archive:
        sdist_names = set(archive.getnames())
    prefix = next(name.split("/", 1)[0] for name in sdist_names)
    required_build_inputs = {
        f"{prefix}/pyproject.toml",
        f"{prefix}/setup.py",
        f"{prefix}/yupp.pth",
        f"{prefix}/src/yupp/_site.py",
    }
    assert required_build_inputs <= sdist_names
    assert not any("/package/" in name or "/script/pkg-" in name for name in sdist_names)
    assert not any(name.endswith((".whl", ".tar.gz")) for name in sdist_names)


def _install_wheel(tmp_path, wheel, interpreter=sys.executable):
    venv = tmp_path / "venv"
    _run([interpreter, "-m", "venv", venv], cwd=tmp_path)
    python = _python_in(venv)
    _run(
        [python, "-m", "pip", "install", "--no-index", "--no-deps", wheel],
        cwd=tmp_path,
    )
    return venv, python


def _exercise_clean_install(tmp_path, wheel, interpreter=sys.executable):
    venv, python = _install_wheel(tmp_path, wheel, interpreter)
    hostile = tmp_path / "hostile"
    hostile.mkdir()
    sentinel = hostile / "sentinel"
    (hostile / "yupp.py").write_text(
        "from pathlib import Path\n"
        f"Path({str(sentinel)!r}).write_text('executed')\n"
        "raise RuntimeError('hostile cwd yupp.py executed')\n",
        encoding="utf8",
    )
    (hostile / "runpy.py").write_text(
        "from pathlib import Path\n"
        f"Path({str(sentinel)!r}).write_text('executed')\n"
        "raise RuntimeError('hostile cwd runpy.py executed')\n",
        encoding="utf8",
    )

    location = _run(
        [
            python,
            "-c",
            "import logging,pathlib,sys,yupp; "
            "root=pathlib.Path(sys.prefix).resolve(); "
            "installed=pathlib.Path(yupp.__file__).resolve(); "
            "assert installed.is_relative_to(root); "
            "assert 'yupp.pp.yugen' not in sys.modules; "
            "assert sys.getrecursionlimit() == 1000; "
            "assert not logging.getLogger('log').handlers; "
            "assert not logging.getLogger('trace').handlers; "
            "print(installed)",
        ],
        cwd=hostile,
    )
    assert str(REPO_ROOT) not in location.stdout
    assert not sentinel.exists()

    sources = {
        "utf8.py": "# coding: yupp\n($set value 'utf8')\nprint(($value))\n".encode(),
        "cp1252.py": "# coding: yupp.cp1252\nprint('café')\n".encode("cp1252"),
        "shape.py": b"#!/usr/bin/env python\r\n# coding: yupp\r\nprint('shape')",
    }
    expected = {"utf8.py": "utf8\n", "cp1252.py": "caf\N{LATIN SMALL LETTER E WITH ACUTE}\n", "shape.py": "shape\n"}
    for name, raw in sources.items():
        source = hostile / name
        source.write_bytes(raw)
        process = _run([python, source], cwd=hostile)
        assert process.stdout == expected[name]
        assert not sentinel.exists()

    module = _run([python, "-m", "yupp", "--version"], cwd=hostile)
    console = _run([_console_in(venv), "--version"], cwd=hostile)
    assert module.stdout.strip() == "yupp 1.2c1"
    assert console.stdout.strip() == "yupp 1.2c1"
    _run(
        [python, "-c", "import yupp; assert callable(yupp.cli) and callable(yupp.translate)"],
        cwd=hostile,
    )

    resource_source = hostile / "resource.yu-py"
    resource_source.write_text("($import coroutine-py)\nprint('resources')\n", encoding="utf8")
    _run(
        [_console_in(venv), "-q", "--no-read-only", resource_source],
        cwd=hostile,
    )
    generated = hostile / "resource.py"
    assert generated.exists()
    assert "print('resources')" in generated.read_text(encoding="utf8")

    broken = hostile / "broken.yu-py"
    broken.write_text("($set missing", encoding="utf8")
    failure = subprocess.run(
        [str(_console_in(venv)), "-q", "--no-read-only", str(broken)],
        cwd=hostile,
        env=_clean_environment(),
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert failure.returncode == 4
    assert not sentinel.exists()
    return venv, python


@pytest.mark.packaging
def test_wheel_clean_install_codec_cli_resources_and_shadow_safety(
    tmp_path, distributions
):
    wheel, _ = distributions
    _exercise_clean_install(tmp_path, wheel)


@pytest.mark.packaging
def test_sdist_rebuild_has_equivalent_wheel_and_installs(tmp_path, distributions):
    wheel, sdist = distributions
    extracted = tmp_path / "extracted"
    extracted.mkdir()
    with tarfile.open(sdist, "r:gz") as archive:
        archive.extractall(extracted, filter="data")
    project = next(extracted.iterdir())
    rebuilt = tmp_path / "rebuilt"
    rebuilt.mkdir()
    _run(
        [sys.executable, "-m", "build", "--no-isolation", "--wheel", "--outdir", rebuilt],
        cwd=project,
    )
    rebuilt_wheel = next(rebuilt.glob("*.whl"))
    assert _normalized_wheel_payload(rebuilt_wheel) == _normalized_wheel_payload(wheel)
    install = tmp_path / "install"
    install.mkdir()
    _exercise_clean_install(install, rebuilt_wheel)


@pytest.mark.packaging
def test_uninstall_removes_startup_hook_and_codec(tmp_path, distributions):
    wheel, _ = distributions
    venv, python = _install_wheel(tmp_path, wheel)
    site_packages = _run(
        [python, "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"],
        cwd=tmp_path,
    ).stdout.strip()
    hook = Path(site_packages) / "yupp.pth"
    assert hook.is_file()

    _run([python, "-m", "pip", "uninstall", "-y", "yupp"], cwd=tmp_path)
    assert not hook.exists()
    unavailable = subprocess.run(
        [
            str(python),
            "-c",
            "import codecs; codecs.lookup('yupp')",
        ],
        cwd=tmp_path,
        env=_clean_environment(),
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert unavailable.returncode != 0
    assert "unknown encoding" in unavailable.stderr.lower()


@pytest.mark.packaging
def test_local_supported_interpreters_accept_the_wheel(tmp_path, distributions):
    wheel, _ = distributions
    candidates = [shutil.which(f"python3.{minor}") for minor in range(11, 15)]
    interpreters = tuple(dict.fromkeys(candidate for candidate in candidates if candidate))
    assert interpreters, "no supported CPython interpreter is available"
    for index, interpreter in enumerate(interpreters):
        case = tmp_path / f"python-{index}"
        case.mkdir()
        venv, python = _install_wheel(case, wheel, interpreter)
        source = case / "first-process.py"
        source.write_bytes(b"# coding: yupp\nprint('supported')\n")
        process = _run([python, source], cwd=case)
        assert process.stdout == "supported\n"
        assert venv.is_dir()
