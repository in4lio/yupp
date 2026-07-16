from pathlib import Path
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from urllib.parse import unquote, urlsplit

import pytest

from tests.conftest import REPO_ROOT


ACTIVE_ROOTS = (
    REPO_ROOT / "src" / "yupp",
    REPO_ROOT / "doc",
    REPO_ROOT / "eg",
    REPO_ROOT / "sublime_text",
    REPO_ROOT / "tests",
)
ACTIVE_FILES = (
    REPO_ROOT / "README.md",
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

INLINE_MARKDOWN_LINK = re.compile(r"!?\[[^]]*\]\(([^)]+)\)")
REFERENCE_MARKDOWN_LINK = re.compile(r"(?<!!)\[([^]\n]+)\]\[([^]\n]*)\]")
SHORTCUT_REFERENCE_MARKDOWN_LINK = re.compile(
    r"(?<![!\]])\[([^]\n]+)\](?![\[(:])"
)
REFERENCE_MARKDOWN_DEFINITION = re.compile(
    r"(?m)^[ \t]{0,3}\[([^]\n]+)\]:[ \t]*(?:<([^>\n]+)>|(\S+))"
)
MARKDOWN_HEADING_LINK = re.compile(r"!?\[([^]\n]*)\]\([^)]+\)")
MARKDOWN_FENCE = re.compile(r"^[ ]{0,3}(`{3,}|~{3,})")
MARKDOWN_HEADING = re.compile(r"^[ ]{0,3}#{1,6}[ \t]+(.+?)[ \t]*#*[ \t]*$")


def _reference_label(label):
    return " ".join(label.split()).casefold()


def _markdown_destination(raw_target):
    raw_target = raw_target.strip()
    if raw_target.startswith("<"):
        closing_bracket = raw_target.find(">")
        if closing_bracket >= 0:
            return raw_target[1:closing_bracket]
    return raw_target.split(maxsplit=1)[0]


def _markdown_targets(text):
    definitions = {}
    for match in REFERENCE_MARKDOWN_DEFINITION.finditer(text):
        definitions.setdefault(
            _reference_label(match.group(1)), match.group(2) or match.group(3)
        )

    for match in INLINE_MARKDOWN_LINK.finditer(text):
        yield _markdown_destination(match.group(1))

    for match in REFERENCE_MARKDOWN_LINK.finditer(text):
        label = match.group(2) or match.group(1)
        target = definitions.get(_reference_label(label))
        if target is not None:
            yield target

    for match in SHORTCUT_REFERENCE_MARKDOWN_LINK.finditer(text):
        target = definitions.get(_reference_label(match.group(1)))
        if target is not None:
            yield target


def _markdown_anchor(heading):
    heading = MARKDOWN_HEADING_LINK.sub(r"\1", heading)
    heading = re.sub(r"<[^>]+>", "", heading)
    heading = re.sub(r"[\\`*~]", "", heading).casefold()
    heading = "".join(
        character
        for character in heading
        if character.isalnum() or character in " _-"
    )
    return re.sub(r"\s+", "-", heading.strip())


def _markdown_anchors(text):
    anchors = set()
    fence = None
    for line in text.splitlines():
        fence_match = MARKDOWN_FENCE.match(line)
        if fence_match:
            marker = fence_match.group(1)
            if fence is None:
                fence = (marker[0], len(marker))
            elif marker[0] == fence[0] and len(marker) >= fence[1]:
                fence = None
            continue
        if fence is not None:
            continue

        heading_match = MARKDOWN_HEADING.match(line)
        if heading_match is None:
            continue
        anchor = _markdown_anchor(heading_match.group(1))
        if not anchor:
            continue
        candidate = anchor
        suffix = 0
        while candidate in anchors:
            suffix += 1
            candidate = f"{anchor}-{suffix}"
        anchors.add(candidate)
    return anchors


def _missing_markdown_targets(path, text, anchor_cache=None):
    if anchor_cache is None:
        anchor_cache = {}

    missing = []
    for target in _markdown_targets(text):
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc:
            continue

        relative = unquote(parsed.path)
        target_path = (path if not relative else path.parent / relative).resolve()
        if not target_path.exists():
            missing.append(target)
            continue

        fragment = unquote(parsed.fragment)
        if not fragment or target_path.suffix.casefold() != ".md":
            continue
        anchors = anchor_cache.get(target_path)
        if anchors is None:
            anchors = _markdown_anchors(target_path.read_text(encoding="utf8"))
            anchor_cache[target_path] = anchors
        if fragment not in anchors:
            missing.append(target)

    return missing


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
    assert not (REPO_ROOT / "docs").exists()
    assert not (REPO_ROOT / "package").exists()
    assert not (REPO_ROOT / "project").exists()
    assert not list((REPO_ROOT / "script").glob("pkg-*"))
    assert not (REPO_ROOT / "eg" / "test.sh").exists()

    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf8")
    assert 'readme = { file = "README.md"' in pyproject


@pytest.mark.parametrize(
    ("link", "definition"),
    (
        ("[guide][g]", "[g]: missing.md"),
        ("[guide][]", "[guide]: missing.md"),
        ("[guide]", "[guide]: missing.md"),
    ),
)
def test_markdown_reference_links_cannot_hide_missing_local_target(
    tmp_path, link, definition
):
    path = tmp_path / "README.md"
    text = f"{link}\n\n{definition}\n"
    path.write_text(text, encoding="utf8")

    assert _missing_markdown_targets(path, text) == ["missing.md"]


@pytest.mark.parametrize("target", ("#missing", "other.md#missing"))
def test_markdown_links_cannot_hide_missing_heading(tmp_path, target):
    path = tmp_path / "README.md"
    text = f"# Present\n\n[missing]({target})\n"
    path.write_text(text, encoding="utf8")
    (tmp_path / "other.md").write_text("# Present\n", encoding="utf8")

    assert _missing_markdown_targets(path, text) == [target]


def test_markdown_anchor_normalizer_matches_repository_headings():
    assert _markdown_anchor("INT_MAX, INT_MIN") == "int_max-int_min"
    assert (
        _markdown_anchor("Standard Library ([stdlib.yu](./stdlib.yu))")
        == "standard-library-stdlibyu"
    )


def test_documentation_local_links_resolve(active_text_files):
    missing = []
    anchor_cache = {}
    for path, text in active_text_files:
        if path.suffix != ".md":
            continue
        missing.extend(
            f"{path.relative_to(REPO_ROOT)} -> {target}"
            for target in _missing_markdown_targets(path, text, anchor_cache)
        )

    assert not missing, "broken local documentation links: " + ", ".join(missing)


def test_active_files_do_not_reference_removed_root_entrypoints(active_text_files):
    findings = []
    for path, text in active_text_files:
        if "yup.py" in text or "$(YUPP_HOME)/lib" in text or "../lib/" in text:
            findings.append(str(path.relative_to(REPO_ROOT)))
    assert not findings, f"stale pre-src paths: {', '.join(findings)}"


@pytest.mark.parametrize(
    "path",
    (
        REPO_ROOT / "README.md",
        REPO_ROOT / "doc" / "README.md",
        REPO_ROOT / "doc" / "python.md",
    ),
)
def test_user_guides_document_open_ended_python_floor(path):
    documentation = path.read_text(encoding="utf8").lower()

    assert "3.11 or newer" in documentation
    assert "2.0rc1" not in documentation
    for obsolete in (
        "3.11-3.14",
        "3.11, 3.12, 3.13, and 3.14",
        "3.15 prerelease",
    ):
        assert obsolete not in documentation


def test_documented_python3_contract_covers_installation_and_limits():
    documentation = "\n".join(
        [
            (REPO_ROOT / "README.md").read_text(encoding="utf8"),
            (REPO_ROOT / "doc" / "README.md").read_text(encoding="utf8"),
            (REPO_ROOT / "doc" / "python.md").read_text(encoding="utf8"),
        ]
    ).lower()

    for required in (
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


def test_migration_details_have_one_canonical_guide():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf8").lower()
    migration = (REPO_ROOT / "doc" / "yueval-migration.md").read_text(
        encoding="utf8"
    ).lower()

    assert "[migration guide](doc/yueval-migration.md)" in readme
    assert "when upgrading from the python 2-compatible release" not in readme
    for required in (
        "## security boundary",
        "## python 3 project migration",
        "future",
        "past",
        "force = true",
        "## runtime migration warning",
        "## compatibility delta",
    ):
        assert required in migration


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
    assert process.stdout.strip() == "yupp 2.0rc1"


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


def test_prerelease_identity_matches_source_and_metadata():
    metadata = (REPO_ROOT / "src" / "yupp" / "_metadata.py").read_text(
        encoding="utf8"
    )
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf8")

    assert "VERSION = '2.0rc1'" in metadata
    assert 'version = "2.0rc1"' in pyproject
