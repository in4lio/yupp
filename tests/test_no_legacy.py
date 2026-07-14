from pathlib import Path
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

from tests.conftest import REPO_ROOT


ACTIVE_ROOTS = (
    REPO_ROOT / "src" / "yupp",
    REPO_ROOT / "eg",
    REPO_ROOT / "project",
    REPO_ROOT / "sublime_text",
    REPO_ROOT / "tests",
)
ACTIVE_FILES = (
    REPO_ROOT / "README.md",
    REPO_ROOT / "doc" / "README.md",
    REPO_ROOT / "doc" / "builtin.md",
    REPO_ROOT / "doc" / "glance.md",
    REPO_ROOT / "doc" / "python.md",
    REPO_ROOT / "pyproject.toml",
    REPO_ROOT / "setup.py",
    REPO_ROOT / "yupp.pth",
)

IGNORED_PARTS = {"__pycache__", ".pytest_cache"}
IGNORED_SUFFIXES = {".bak", ".pyc", ".json"}

FORBIDDEN_ACTIVE_PATTERNS = {
    "compatibility package import": re.compile(
        r"(?m)^\s*(?:from|import)\s+(?:future|past|builtins)(?:\.|\s|$)"
    ),
    "compatibility future import": re.compile(
        r"(?m)^\s*from\s+__future__\s+import\s+"
    ),
    "removed imp module": re.compile(r"(?m)^\s*(?:from\s+imp|import\s+imp)(?:\s|$)"),
    "stdlib distutils": re.compile(r"\bdistutils\b"),
    "execfile call": re.compile(r"\bexecfile\s*\("),
    "xrange call": re.compile(r"\bxrange\s*\("),
    "Python 2 branch marker": re.compile(r"\b(?:PY2|python2)\b", re.IGNORECASE),
    "version split branch": re.compile(
        r"sys\.version_info(?:\s*\[\s*0\s*\])?\s*(?:<|<=|==|!=|>=|>)\s*3"
    ),
    "Python 2 ConfigParser import": re.compile(
        r"(?m)^\s*from\s+ConfigParser\s+import\s+"
    ),
}


def _active_text_files():
    paths = list(ACTIVE_FILES)
    for root in ACTIVE_ROOTS:
        paths.extend(path for path in root.rglob("*") if path.is_file())
    for path in sorted(set(paths)):
        if path == Path(__file__):
            # This guard test necessarily contains the signatures it rejects.
            continue
        if IGNORED_PARTS.intersection(path.parts):
            continue
        if path.suffix in IGNORED_SUFFIXES:
            continue
        try:
            yield path, path.read_text(encoding="utf8")
        except UnicodeDecodeError:
            # Active binary assets are outside a source-compatibility scan.
            continue


@pytest.fixture(scope="session")
def active_text_files():
    return tuple(_active_text_files())


@pytest.mark.parametrize("label,pattern", FORBIDDEN_ACTIVE_PATTERNS.items())
def test_active_sources_have_no_python2_compatibility_constructs(
    label, pattern, active_text_files
):
    findings = []
    for path, text in active_text_files:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append(f"{path.relative_to(REPO_ROOT)}:{line}")
    assert not findings, f"{label}: {', '.join(findings)}"


def test_canonical_documentation_and_packaging_surfaces_are_unique():
    assert (REPO_ROOT / "README.md").is_file()
    assert not (REPO_ROOT / "README").exists()
    assert (REPO_ROOT / "doc" / "README.md").is_file()
    assert not (REPO_ROOT / "doc" / "README").exists()
    assert not (REPO_ROOT / "package").exists()
    assert not list((REPO_ROOT / "script").glob("pkg-*"))

    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf8")
    assert 'readme = { file = "README.md"' in pyproject


def test_active_files_do_not_reference_removed_root_entrypoints(active_text_files):
    findings = []
    for path, text in active_text_files:
        if "yup.py" in text or "$(YUPP_HOME)/lib" in text or "../lib/" in text:
            findings.append(str(path.relative_to(REPO_ROOT)))
    assert not findings, f"stale pre-src paths: {', '.join(findings)}"


def test_documented_python3_contract_covers_installation_and_limits():
    documentation = "\n".join(
        [
            (REPO_ROOT / "README.md").read_text(encoding="utf8"),
            (REPO_ROOT / "doc" / "README.md").read_text(encoding="utf8"),
            (REPO_ROOT / "doc" / "python.md").read_text(encoding="utf8"),
        ]
    ).lower()

    for required in (
        "3.11",
        "3.12",
        "3.13",
        "3.14",
        "3.15",
        "python -m pip install",
        "wheel",
        "direct main",
        "imported modules",
        "python -s",
        "pipx",
        ".yuconfig",
        "trusted",
        "python -m pytest",
        "python -m build",
    ):
        assert required in documentation


def test_documented_module_version_command_runs():
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(REPO_ROOT / "src")

    process = subprocess.run(
        [sys.executable, "-S", "-m", "yupp", "--version"],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert process.returncode == 0, process.stderr
    assert process.stdout.strip() == "yupp 1.2c1"


def test_bundled_editor_python_surface_is_python3():
    plugin = REPO_ROOT / "sublime_text" / "Data" / "Packages" / "yupp" / "yupp.py"
    compile(plugin.read_text(encoding="utf8"), str(plugin), "exec")

    grammar = (
        REPO_ROOT
        / "sublime_text"
        / "Data"
        / "Packages"
        / "User"
        / "Python (yupp).tmLanguage"
    )
    tree = ET.parse(grammar)
    match_patterns = []
    for dictionary in tree.iter("dict"):
        children = list(dictionary)
        for index, child in enumerate(children[:-1]):
            if child.tag == "key" and child.text == "match":
                match_patterns.append(children[index + 1].text or "")

    legacy_editor_tokens = re.compile(
        r"\b(?:execfile|raw_input|basestring|buffer|long|xrange|nonzero|unichr|coerce)\b"
    )
    assert not [
        pattern for pattern in match_patterns if legacy_editor_tokens.search(pattern)
    ]


def test_prerelease_identity_is_unchanged_in_source_and_metadata():
    metadata = (REPO_ROOT / "src" / "yupp" / "_metadata.py").read_text(
        encoding="utf8"
    )
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf8")

    assert "VERSION = '1.2c1'" in metadata
    assert 'version = "1.2c1"' in pyproject
