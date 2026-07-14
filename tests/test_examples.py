import os
import re
import shutil

import pytest

from yupp.pp import yup
from tests.conftest import REPO_ROOT


EXAMPLES = REPO_ROOT / "eg"
GENERATED_SUFFIXES = {".c", ".cpp", ".h", ".py"}

EXAMPLE_CASES = [
    ("app/co.yu-c", ("app/co.c",)),
    ("app/co.yu-h", ("app/co.h",)),
    ("app/main.yu-c", ("app/main.c",)),
    ("argv.yu-c", ("argv.c",)),
    ("coding.yu-py", ("coding.py",)),
    ("coro.py", ("coro.yugen.py",)),
    ("coro.yu-c", ("coro.c",)),
    ("dict.yu-c", ("dict.c",)),
    ("dict.yu-py", ("dict.py",)),
    ("glance/glance.yu-cpp", ("glance/glance.cpp",)),
    ("glance/glance.yu-py", ("glance/glance.py",)),
    ("gpio.yu-c", ("gpio.c",)),
    ("hello.yu-c", ("hello.c",)),
    ("passage.yu-c", ("passage-a.c", "passage-b.c", "passage-c.c")),
    ("switch.py", ("switch.yugen.py",)),
    ("ulam.yu-c", ("ulam.c",)),
    ("unfold.yu-c", ("unfold.c",)),
]


def declared_example_outputs():
    return {output for _source, outputs in EXAMPLE_CASES for output in outputs}


def generated_example_inventory(root):
    declared_sources = {source for source, _outputs in EXAMPLE_CASES}
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix in GENERATED_SUFFIXES
        and path.relative_to(root).as_posix() not in declared_sources
    }


def normalize_declared_timestamp_fragments(content):
    """Normalize only timestamps emitted by a no-argument ``$__TITLE__``."""
    return re.sub(
        rb"( out of [^\r\n]{1,200}) at \d{4}-\d{2}-\d{2} \d{2}:\d{2}(?::\d{2})?",
        rb"\1 at <DATETIME>",
        content,
    )


def isolated_examples(tmp_path):
    destination = tmp_path / "eg"
    shutil.copytree(
        EXAMPLES,
        destination,
        ignore=shutil.ignore_patterns("*.bak", "*.json", "*.pyc", "__pycache__"),
    )
    return destination


@pytest.mark.integration
@pytest.mark.parametrize(
    "source_name,output_names",
    EXAMPLE_CASES,
    ids=[source for source, _outputs in EXAMPLE_CASES],
)
def test_tracked_example_regenerates_deterministically(
    source_name, output_names, tmp_path, monkeypatch
):
    workspace = isolated_examples(tmp_path)
    source = workspace / source_name
    monkeypatch.chdir(workspace)

    # A copied golden may be newer than its source. Set explicit relative
    # mtimes so this test exercises expansion rather than a cache hit.
    for output_name in output_names:
        os.utime(workspace / output_name, ns=(1_000_000_000, 1_000_000_000))
    os.utime(source, ns=(2_000_000_000, 2_000_000_000))

    status = yup.cli(["-q", "--no-read-only", "--pp-no-browse", str(source)])

    assert status == 0
    for output_name in output_names:
        actual = normalize_declared_timestamp_fragments(
            (workspace / output_name).read_bytes()
        )
        expected = normalize_declared_timestamp_fragments(
            (EXAMPLES / output_name).read_bytes()
        )
        assert actual == expected


@pytest.mark.integration
def test_sequential_files_do_not_share_evaluator_bindings(tmp_path, monkeypatch):
    first = tmp_path / "first.yu-c"
    second = tmp_path / "second.yu-c"
    first.write_text("($set cross_file 17)FIRST=($cross_file)", encoding="utf8")
    second.write_text("SECOND=($cross_file)", encoding="utf8")
    monkeypatch.chdir(tmp_path)

    status = yup.cli(["-q", "--no-read-only", str(first), str(second)])

    assert status == 0
    assert (tmp_path / "first.c").read_text(encoding="utf8") == "FIRST=17\n"
    assert (tmp_path / "second.c").read_text(encoding="utf8") == "SECOND=cross_file\n"


def test_example_matrix_covers_every_tracked_generated_file():
    assert declared_example_outputs() == generated_example_inventory(EXAMPLES)


def test_example_inventory_finds_generated_artifact_omitted_from_cases(
    tmp_path,
):
    workspace = isolated_examples(tmp_path)
    omitted = workspace / "nested" / "omitted.cpp"
    omitted.parent.mkdir()
    omitted.write_text("// generated but undeclared\n", encoding="utf8")

    undeclared = generated_example_inventory(workspace) - declared_example_outputs()

    assert undeclared == {"nested/omitted.cpp"}


def test_example_checks_never_target_repository_outputs():
    assert all((EXAMPLES / source).is_file() for source, _outputs in EXAMPLE_CASES)
