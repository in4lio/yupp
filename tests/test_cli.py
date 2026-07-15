import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import traceback

import pytest

from yupp.pp import yup
from tests.conftest import REPO_ROOT


@pytest.mark.parametrize(
    "source_name,output_name",
    [
        ("name", "name.yugen"),
        ("name.c", "name.yugen.c"),
        ("name.yu-c", "name.c"),
        ("name.yu", "name.yugen"),
        ("name.part.yu", "name.part"),
        ("NAME.YU-PY", "NAME.PY"),
    ],
)
def test_output_name_table(source_name, output_name):
    assert yup._output_fn(source_name) == output_name


def test_output_name_uses_only_basename_in_output_directory(tmp_path):
    yup.shell.output_dir = str(tmp_path / "generated")

    assert yup._output_fn("nested/source.yu-c") == str(tmp_path / "generated" / "source.c")


def test_dynamic_scope_migration_warning_cli_is_opt_in():
    defaults = yup.shell_parse_cli_arguments([])
    enabled = yup.shell_parse_cli_arguments(["-Wdynamic-scope"])
    disabled = yup.shell_parse_cli_arguments(
        ["-Wdynamic-scope", "-Wno-dynamic-scope"]
    )

    assert defaults.warn_dynamic_scope is False
    assert enabled.warn_dynamic_scope is True
    assert disabled.warn_dynamic_scope is False


def test_dynamic_scope_migration_warning_can_be_enabled_in_yuconfig(
    tmp_path, monkeypatch
):
    source = tmp_path / "migration.yu-c"
    source.write_text("TEXT", encoding="utf8")
    (tmp_path / "migration.yuconfig").write_text(
        "warn_dynamic_scope = True\n", encoding="utf8"
    )
    monkeypatch.chdir(tmp_path)

    config = yup.shell_parse_yuconfig(str(source))
    yup._pp_configure(config)

    assert config["warn_dynamic_scope"] is True
    assert yup.config.warn_dynamic_scope is True


@pytest.mark.integration
def test_global_and_file_configuration_precedence(tmp_path, monkeypatch):
    source = tmp_path / "unit.yu-c"
    source.write_text("TEXT", encoding="utf8")
    (tmp_path / ".yuconfig").write_text(
        "log_level = LOG_LEVEL_ERROR\n"
        "directory.append('global-dir')\n"
        "pp_define.append('GLOBAL:1')\n",
        encoding="utf8",
    )
    (tmp_path / "unit.yuconfig").write_text(
        "log_level = LOG_LEVEL_INFO\n"
        "directory.append('file-dir')\n"
        "pp_define.append('FILE:2')\n",
        encoding="utf8",
    )
    monkeypatch.chdir(tmp_path)

    config = yup.shell_parse_yuconfig(str(source))

    assert config["log_level"] == yup.LOG_LEVEL_INFO
    assert config["directory"] == ["global-dir", "file-dir"]
    assert config["pp_define"] == ["GLOBAL:1", "FILE:2"]


@pytest.mark.integration
def test_configuration_scripts_share_globals_and_keep_real_filenames(tmp_path, monkeypatch):
    source = tmp_path / "shared.yu-c"
    source.write_text("TEXT", encoding="utf8")
    global_config = tmp_path / ".yuconfig"
    file_config = tmp_path / "shared.yuconfig"
    global_config.write_text(
        "prefix = 'SHARED'\n"
        "def define(value):\n"
        "    pp_define.append(prefix + ':' + value)\n",
        encoding="utf8",
    )
    file_config.write_text("define('VALUE')\nraise RuntimeError('stop')\n", encoding="utf8")
    captured_tracebacks = []

    def capture_error(*_args, **_kwargs):
        captured_tracebacks.append(sys.exc_info()[2])

    monkeypatch.setattr(yup.log, "error", capture_error)
    monkeypatch.chdir(tmp_path)

    config = yup.shell_parse_yuconfig(str(source))

    assert config["pp_define"] == ["SHARED:VALUE"]
    frames = traceback.extract_tb(captured_tracebacks[-1])
    assert frames[-1].filename == str(file_config)


@pytest.mark.integration
def test_configuration_script_honors_its_python_encoding_cookie(tmp_path, monkeypatch):
    source = tmp_path / "encoded.yu-c"
    source.write_text("TEXT", encoding="utf8")
    config_file = tmp_path / "encoded.yuconfig"
    config_file.write_bytes(
        "# coding: latin-1\npp_define.append('café')\n".encode("latin-1")
    )
    monkeypatch.chdir(tmp_path)

    config = yup.shell_parse_yuconfig(str(source))

    assert config["pp_define"] == ["café"]


@pytest.mark.integration
def test_dependency_cache_hit_and_source_miss(tmp_path, monkeypatch):
    source = tmp_path / "cache.yu-c"
    source.write_text("FIRST", encoding="utf8")
    monkeypatch.chdir(tmp_path)

    with source.open() as stream:
        first = yup.proc_stream(stream, str(source))
    output = Path(first[2])
    assert first[:2] == (True, "FIRST\n")
    assert output.read_text(encoding="utf8") == "FIRST\n"

    with source.open() as stream:
        hit = yup.proc_stream(stream, str(source))
    assert hit == (True, "FIRST\n", str(output), 2)

    output.chmod(stat.S_IWRITE | stat.S_IREAD)
    source.write_text("SECOND", encoding="utf8")
    newer = output.stat().st_mtime + 2
    os.utime(source, (newer, newer))
    with source.open() as stream:
        miss = yup.proc_stream(stream, str(source))

    assert miss[:2] == (True, "SECOND\n")
    assert output.read_text(encoding="utf8") == "SECOND\n"
    assert Path(str(output) + ".bak").read_text(encoding="utf8") == "FIRST\n"


def _assert_loaded_config_invalidates_cache(tmp_path, monkeypatch, config_name):
    source = tmp_path / "configured.yu-c"
    source.write_text("($CACHE_VALUE)", encoding="utf8")
    config_file = tmp_path / config_name
    config_file.write_text(
        "pp_define.append('CACHE_VALUE:first')\n", encoding="utf8"
    )
    monkeypatch.chdir(tmp_path)

    with source.open() as stream:
        first = yup.proc_stream(stream, str(source))
    output = Path(first[2])
    assert first[:2] == (True, "first\n")

    config_file.write_text(
        "pp_define.append('CACHE_VALUE:second')\n", encoding="utf8"
    )
    newer = output.stat().st_mtime + 2
    os.utime(config_file, (newer, newer))
    with source.open() as stream:
        second = yup.proc_stream(stream, str(source))

    assert second[:2] == (True, "second\n")
    assert output.read_text(encoding="utf8") == "second\n"
    assert Path(str(output) + ".bak").read_text(encoding="utf8") == "first\n"


@pytest.mark.integration
def test_changed_global_configuration_invalidates_cache(tmp_path, monkeypatch):
    _assert_loaded_config_invalidates_cache(tmp_path, monkeypatch, ".yuconfig")


@pytest.mark.integration
def test_changed_source_configuration_invalidates_cache(tmp_path, monkeypatch):
    _assert_loaded_config_invalidates_cache(
        tmp_path, monkeypatch, "configured.yuconfig"
    )


@pytest.mark.integration
def test_non_ascii_cache_hit_reads_generated_utf8(tmp_path, monkeypatch):
    source = tmp_path / "unicode-cache.yu-c"
    source.write_text("café", encoding="utf8")
    monkeypatch.chdir(tmp_path)

    with source.open() as stream:
        first = yup.proc_stream(stream, str(source))
    output = Path(first[2])
    assert first[:2] == (True, "café\n")
    older = output.stat().st_mtime - 2
    os.utime(source, (older, older))
    real_open = open

    def locale_default_open(filename, mode="r", *args, **kwargs):
        if os.fspath(filename) == str(output) and mode == "r":
            kwargs.setdefault("encoding", "cp1252")
        return real_open(filename, mode, *args, **kwargs)

    monkeypatch.setattr(yup, "open", locale_default_open, raising=False)
    with source.open() as stream:
        cached = yup.proc_stream(stream, str(source))

    assert cached[:2] == (True, "café\n")


@pytest.mark.integration
def test_force_configuration_bypasses_fresh_cache(tmp_path, monkeypatch):
    source = tmp_path / "forced.yu-c"
    output = tmp_path / "forced.c"
    source.write_text("SOURCE", encoding="utf8")
    output.write_text("STALE-CACHE", encoding="utf8")
    newer = source.stat().st_mtime + 10
    os.utime(output, (newer, newer))
    (tmp_path / "forced.yuconfig").write_text("force = True\n", encoding="utf8")
    monkeypatch.chdir(tmp_path)

    with source.open() as stream:
        result = yup.proc_stream(stream, str(source))

    assert result[:2] == (True, "SOURCE\n")
    assert output.read_text(encoding="utf8") == "SOURCE\n"
    assert Path(str(output) + ".bak").read_text(encoding="utf8") == "STALE-CACHE"


@pytest.mark.integration
def test_newer_configured_dependency_invalidates_cache(tmp_path, monkeypatch):
    source = tmp_path / "dependent.yu-c"
    dependency = tmp_path / "dependency.txt"
    source.write_text("DEPENDENT", encoding="utf8")
    dependency.write_text("v1", encoding="utf8")
    (tmp_path / "dependent.yuconfig").write_text(
        "dependency.append('dependency.txt')\n", encoding="utf8"
    )
    monkeypatch.chdir(tmp_path)

    with source.open() as stream:
        first = yup.proc_stream(stream, str(source))
    output = Path(first[2])
    newer = output.stat().st_mtime + 2
    dependency.write_text("v2", encoding="utf8")
    os.utime(dependency, (newer, newer))

    with source.open() as stream:
        second = yup.proc_stream(stream, str(source))

    assert second[:2] == (True, "DEPENDENT\n")
    assert Path(str(output) + ".bak").read_text(encoding="utf8") == "DEPENDENT\n"


@pytest.mark.integration
def test_cli_backup_read_only_and_browse_json(tmp_path, monkeypatch):
    source = tmp_path / "browse.yu-c"
    output = tmp_path / "browse.c"
    source.write_text("BROWSE", encoding="utf8")
    output.write_text("OLD", encoding="utf8")
    monkeypatch.chdir(tmp_path)

    status = yup.cli(["-q", "--pp-browse", str(source)])

    assert status == 0
    assert output.read_text(encoding="utf8") == "BROWSE"
    assert Path(str(output) + ".bak").read_text(encoding="utf8") == "OLD"
    assert not (output.stat().st_mode & stat.S_IWUSR)
    browse = json.loads(Path(str(output) + ".json").read_text(encoding="utf8"))
    assert sorted(browse) == ["browse", "files", "offset"]
    assert browse["files"] == [str(source)]
    assert isinstance(browse["browse"], list)
    assert isinstance(browse["offset"], list)


@pytest.mark.integration
def test_output_write_failure_restores_previous_artifact_and_fails_cli(
    tmp_path, monkeypatch
):
    source = tmp_path / "transaction.yu-c"
    output = tmp_path / "transaction.c"
    source.write_text("NEW", encoding="utf8")
    output.write_text("OLD", encoding="utf8")
    newer = output.stat().st_mtime + 2
    os.utime(source, (newer, newer))
    monkeypatch.chdir(tmp_path)

    def fail_after_partial_write(filename, _text):
        Path(filename).write_text("PARTIAL", encoding="utf8")
        raise OSError("simulated disk failure")

    monkeypatch.setattr(yup, "shell_savetofile", fail_after_partial_write)

    status = yup.cli(["-q", "--no-read-only", str(source)])

    assert status == 4
    assert output.read_text(encoding="utf8") == "OLD"
    assert not Path(str(output) + ".bak").exists()


@pytest.mark.integration
def test_response_file_and_inline_input(tmp_path, monkeypatch, capsys):
    source = tmp_path / "response.yu-c"
    source.write_text("RESPONSE", encoding="utf8")
    response = tmp_path / "args.txt"
    response.write_text(f"-q --no-read-only {source}\n", encoding="utf8")

    args = yup.shell_parse_cli_arguments([f"@{response}"])
    assert args.files == [str(source)]
    assert args.quiet is True
    assert args.read_only is False

    monkeypatch.setattr(yup, "shell_input", lambda: yup.REPL_EXIT)
    status = yup.cli(["-q", "-i", "INLINE"])
    output = capsys.readouterr().out
    assert status == 0
    assert "INLINE" in output


def test_argument_error_is_exit_2():
    with pytest.raises(SystemExit) as error:
        yup.shell_parse_cli_arguments(["--trace", "99"])

    assert error.value.code == 2


@pytest.mark.integration
def test_cli_continues_and_returns_four_per_failed_file(tmp_path, monkeypatch):
    bad_one = tmp_path / "bad-one.yu-c"
    good = tmp_path / "good.yu-c"
    bad_two = tmp_path / "bad-two.yu-c"
    bad_one.write_text("($set a", encoding="utf8")
    good.write_text("GOOD", encoding="utf8")
    bad_two.write_text("($div 1 0)", encoding="utf8")
    monkeypatch.chdir(tmp_path)

    status = yup.cli(["-q", "--no-read-only", str(bad_one), str(good), str(bad_two)])

    assert status == 8
    assert (tmp_path / "good.c").read_text(encoding="utf8") == "GOOD\n"


@pytest.mark.integration
def test_cli_import_directory_option_is_used(tmp_path, monkeypatch):
    library_dir = tmp_path / "libraries"
    library_dir.mkdir()
    (library_dir / "external.yu").write_text("($set loaded_value 9)", encoding="utf8")
    source = tmp_path / "uses-import.yu-c"
    source.write_text("($import external)($loaded_value)", encoding="utf8")
    monkeypatch.chdir(tmp_path)

    status = yup.cli(
        ["-q", "--no-read-only", "-d", str(library_dir), str(source)]
    )

    assert status == 0
    assert (tmp_path / "uses-import.c").read_text(encoding="utf8") == "9\n"


@pytest.mark.integration
def test_unhandled_program_execution_error_is_process_exit_1():
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(REPO_ROOT / "src")
    process = subprocess.run(
        [sys.executable, "-c", "from yupp.pp.yup import cli; cli(None)"],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert process.returncode == 1
    assert "TypeError" in process.stderr


@pytest.mark.integration
def test_public_cli_and_translate_return_shapes(tmp_path, monkeypatch):
    import yupp

    assert Path(yupp.__file__).resolve().is_relative_to(REPO_ROOT / "src" / "yupp")

    source = tmp_path / "public.yu-c"
    source.write_text("PUBLIC", encoding="utf8")
    monkeypatch.chdir(tmp_path)

    assert yupp.cli(["-q", "--no-read-only", str(source)]) == 0
    translated = yupp.translate(str(source))
    assert translated == (True, str(tmp_path / "public.c"))


def test_proc_file_closes_its_input_stream(monkeypatch):
    stream = io.StringIO("SOURCE")

    def fake_proc_stream(input_stream, filename):
        assert input_stream is stream
        assert not input_stream.closed
        return (True, "SOURCE\n", filename + ".out", 0)

    monkeypatch.setattr(yup, "open", lambda *_args, **_kwargs: stream, raising=False)
    monkeypatch.setattr(yup, "proc_stream", fake_proc_stream)

    assert yup.proc_file("source.yu") == (True, "source.yu.out")
    assert stream.closed


def test_proc_file_closes_its_input_stream_after_unexpected_failure(monkeypatch):
    stream = io.StringIO("SOURCE")

    def fail(_input_stream, _filename):
        raise RuntimeError("stop")

    monkeypatch.setattr(yup, "open", lambda *_args, **_kwargs: stream, raising=False)
    monkeypatch.setattr(yup, "proc_stream", fail)

    with pytest.raises(RuntimeError, match="stop"):
        yup.proc_file("source.yu")
    assert stream.closed
