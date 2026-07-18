import re

from tests.conftest import REPO_ROOT


WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
PUBLISH_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "publish.yml"

ACTION_PINS = {
    "actions/checkout": "9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0",
    "actions/setup-python": "a309ff8b426b58ec0e2a45f0f869d46889d02405",
    "actions/upload-artifact": "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
    "actions/download-artifact": "3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c",
    "pypa/gh-action-pypi-publish": "cef221092ed1bacb1cc03d23a2d87d1d172e277b",
}


def _workflow_source(path=WORKFLOW):
    return path.read_text(encoding="utf8")


def _assert_actions_are_pinned(source):
    uses_lines = [line.strip() for line in source.splitlines() if "uses:" in line]
    pinned = re.compile(
        r"^uses: ([a-z0-9_-]+/[a-z0-9_-]+)@([0-9a-f]{40}) "
        r"# (v[^ ]+|release/v[0-9]+)$"
    )

    assert uses_lines
    for line in uses_lines:
        match = pinned.fullmatch(line)
        assert match is not None, f"action is not pinned with a tag comment: {line}"
        action, revision, _tag = match.groups()
        assert ACTION_PINS[action] == revision


def test_only_github_actions_is_the_active_ci_surface():
    assert WORKFLOW.is_file()
    assert not (REPO_ROOT / ".travis.yml").exists()


def test_ci_has_read_only_permissions_and_safe_event_inputs():
    source = _workflow_source()

    assert "permissions:\n  contents: read\n" in source
    assert source.count("permissions:") == 1
    assert "pull_request_target" not in source
    assert "workflow_run" not in source
    assert "secrets." not in source
    assert "persist-credentials: false" in source
    assert source.count("persist-credentials: false") == source.count(
        "uses: actions/checkout@"
    )
    assert "cancel-in-progress: true" in source


def test_all_actions_are_pinned_to_reviewed_full_commit_shas():
    _assert_actions_are_pinned(_workflow_source())


def test_ci_reuses_one_exact_distribution_set_for_all_artifact_gates():
    source = _workflow_source()

    assert source.count("python -m build") == 1
    assert source.count("name: distributions") == 4  # one upload, three downloads
    assert source.count("YUPP_DISTRIBUTIONS:") == 3
    assert source.count("${{ github.workspace }}/downloaded-dist") == 3
    assert "needs: build" in source


def test_supported_and_advisory_python_matrices_are_explicit():
    source = _workflow_source()
    supported = 'python-version: ["3.11", "3.12", "3.13", "3.14"]'

    assert source.count(supported) == 2
    assert 'python-version: "3.15-dev"' in source
    assert "allow-prereleases: true" in source
    assert "continue-on-error: true" in source
    assert "if: ${{ always() }}" in source
    assert " -n " not in source


def test_publish_workflow_uses_release_gate_and_trusted_publishing():
    source = _workflow_source(PUBLISH_WORKFLOW)
    event_source = source.split("on:\n", 1)[1].split("\npermissions:\n", 1)[0]

    assert event_source == "  release:\n    types: [published]\n"
    assert "permissions:\n  contents: read\n" in source
    assert source.count("permissions:") == 2
    assert source.count("id-token: write") == 1
    assert "environment:\n      name: pypi" in source
    assert "url: https://pypi.org/p/yupp" in source
    assert "secrets." not in source


def test_publish_workflow_separates_build_from_oidc_publish_job():
    source = _workflow_source(PUBLISH_WORKFLOW)

    build_source, publish_source = source.split("\n  publish:\n", 1)
    assert "python -m build" in build_source
    assert "python -m twine check --strict dist/*" in build_source
    assert "RELEASE_TAG: ${{ github.event.release.tag_name }}" in build_source
    assert ".removeprefix('v')" in build_source
    assert "does not match package version" in build_source
    assert "YUPP_DISTRIBUTIONS: ${{ github.workspace }}/dist" in build_source
    assert build_source.index("python -m build") < build_source.index(
        "python -m pytest"
    )
    assert "id-token: write" not in build_source
    assert "needs: build" in publish_source
    assert "id-token: write" in publish_source
    assert "python -m build" not in publish_source
    assert source.count("name: release-distributions") == 2
    assert "persist-credentials: false" in source
    assert "ref: ${{ github.event.release.tag_name }}" in build_source


def test_publish_actions_are_pinned_to_reviewed_full_commit_shas():
    _assert_actions_are_pinned(_workflow_source(PUBLISH_WORKFLOW))
