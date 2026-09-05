"""Smoke tests for submit50's CLI wiring against lib50.

These run in CI against both the newest lib50 and the minimum version declared in
setup.py, so a lib50 API drift (e.g. a missing ``auth_method`` kwarg) fails the
build instead of every student's submission.
"""
import inspect
import re
import subprocess
import sys

import lib50
import pytest

import submit50.__main__ as cli


def test_lib50_push_accepts_auth_method():
    assert "auth_method" in inspect.signature(lib50.push).parameters


@pytest.mark.parametrize(
    "https, ssh, expected",
    [
        (False, False, None),
        (True, False, "https"),
        (False, True, "ssh"),
        (True, True, None),
    ],
)
def test_resolve_auth_method(https, ssh, expected, capsys):
    assert cli.resolve_auth_method(https, ssh) == expected
    out = capsys.readouterr().out
    if https and ssh:
        assert "--https and --ssh" in out
    else:
        assert out == ""


def _stub_checks(monkeypatch):
    """Skip the network-dependent preflight checks."""
    monkeypatch.setattr(cli, "check_announcements", lambda: None)
    monkeypatch.setattr(cli, "check_version", lambda: None)
    monkeypatch.setattr(cli, "check_slug_year", lambda slug: None)


@pytest.mark.parametrize(
    "flags, expected",
    [
        ([], None),
        (["--https"], "https"),
        (["--ssh"], "ssh"),
        (["--https", "--ssh"], None),
    ],
)
def test_main_passes_auth_method_to_lib50(flags, expected, monkeypatch, capsys):
    _stub_checks(monkeypatch)
    calls = []

    def fake_push(tool, slug, config_loader, **kwargs):
        calls.append((tool, slug, kwargs))
        return "user", "deadbeef", "pushed"

    monkeypatch.setattr(lib50, "push", fake_push)
    monkeypatch.setattr(sys, "argv", ["submit50", *flags, "cs50/problems/2026/x/hello"])

    cli.main()

    assert len(calls) == 1
    tool, slug, kwargs = calls[0]
    assert (tool, slug) == ("submit50", "cs50/problems/2026/x/hello")
    assert kwargs["auth_method"] == expected
    assert kwargs["prompt"] is cli.prompt
    assert "pushed" in capsys.readouterr().out


def test_forced_ssh_failure_gets_actionable_error(monkeypatch):
    _stub_checks(monkeypatch)

    def fail_push(*args, **kwargs):
        raise lib50.ConnectionError  # lib50 raises this bare when a forced SSH login fails

    monkeypatch.setattr(lib50, "push", fail_push)
    monkeypatch.setattr(sys, "argv", ["submit50", "--ssh", "cs50/problems/2026/x/hello"])

    with pytest.raises(cli.Error, match="SSH authentication failed"):
        cli.main()


def test_unforced_connection_error_is_not_rewritten(monkeypatch):
    _stub_checks(monkeypatch)

    def fail_push(*args, **kwargs):
        raise lib50.ConnectionError

    monkeypatch.setattr(lib50, "push", fail_push)
    monkeypatch.setattr(sys, "argv", ["submit50", "cs50/problems/2026/x/hello"])

    with pytest.raises(lib50.ConnectionError):
        cli.main()


def test_rstudio_skips_honesty_prompt(monkeypatch):
    monkeypatch.setenv("RSTUDIO", "1")
    monkeypatch.setattr("builtins.input", lambda *a: pytest.fail("input() must not be called under RSTUDIO"))
    assert cli.prompt(True, ["hello.c"], []) is True


def test_version_output_shape():
    """The release workflow extracts the tag with `cut -d' ' -f2`; keep `<prog> <version>`."""
    out = subprocess.run(
        [sys.executable, "-m", "submit50", "--version"], capture_output=True, text=True, check=True
    ).stdout.strip()
    assert re.fullmatch(r"submit50 \d+\.\d+\.\d+", out), out
