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
import requests

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

    with pytest.raises(cli.Error, match="Could not authenticate with GitHub via SSH") as excinfo:
        cli.main()
    # The same bare ConnectionError is raised when GitHub is unreachable, so the hint must mention connectivity
    assert "online" in str(excinfo.value)


@pytest.mark.parametrize(
    "flags, exc",
    [
        pytest.param([], lib50.ConnectionError(), id="no-flag-bare"),
        pytest.param([], lib50.ConnectionError("Could not connect to GitHub."), id="no-flag-messaged"),
        pytest.param(["--https"], lib50.ConnectionError(), id="https-bare"),
        pytest.param(["--ssh"], lib50.ConnectionError("Could not connect to GitHub due to a SSL error."), id="ssh-messaged"),
    ],
)
def test_connection_error_is_not_rewritten(flags, exc, monkeypatch):
    """Only a *bare* ConnectionError under --ssh is rewritten; everything else passes through untouched."""
    _stub_checks(monkeypatch)

    def fail_push(*args, **kwargs):
        raise exc

    monkeypatch.setattr(lib50, "push", fail_push)
    monkeypatch.setattr(sys, "argv", ["submit50", *flags, "cs50/problems/2026/x/hello"])

    with pytest.raises(lib50.ConnectionError) as excinfo:
        cli.main()
    assert excinfo.value is exc


def test_rstudio_skips_honesty_prompt(monkeypatch):
    monkeypatch.setenv("RSTUDIO", "1")
    monkeypatch.setattr("builtins.input", lambda *a: pytest.fail("input() must not be called under RSTUDIO"))
    assert cli.prompt(True, ["hello.c"], []) is True


@pytest.mark.parametrize(
    "typed, expected",
    [
        ("yes", True),
        ("y", True),
        (" Yes ", True),
        ("no", False),
        ("", False),
        ("yes please", False),
    ],
)
def test_prompt_parses_honesty_answer(typed, expected, monkeypatch):
    monkeypatch.delenv("RSTUDIO", raising=False)
    monkeypatch.setattr("builtins.input", lambda *a: typed)
    assert cli.prompt(True, ["hello.c"], []) is expected


def test_prompt_eof_declines(monkeypatch):
    monkeypatch.delenv("RSTUDIO", raising=False)

    def eof(*a):
        raise EOFError

    monkeypatch.setattr("builtins.input", eof)
    assert cli.prompt(True, ["hello.c"], []) is False


def test_prompt_skips_question_when_no_honesty(monkeypatch):
    monkeypatch.delenv("RSTUDIO", raising=False)
    monkeypatch.setattr("builtins.input", lambda *a: pytest.fail("input() must not be called without an honesty prompt"))
    assert cli.prompt(False, ["hello.c"], []) is True


@pytest.mark.parametrize("typed, aborts", [("yes", False), ("no", True)])
def test_check_slug_year_previous_year_prompts(typed, aborts, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda *a: typed)
    slug = "cs50/problems/2000/x/hello"
    if aborts:
        with pytest.raises(cli.Error, match="User aborted submission"):
            cli.check_slug_year(slug)
    else:
        cli.check_slug_year(slug)


def test_check_slug_year_current_year_does_not_prompt(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda *a: pytest.fail("input() must not be called for a current-year slug"))
    cli.check_slug_year("cs50/problems/9999/x/hello")


# --- packaging ---

def test_python_requires_covers_installed_lib50():
    """The declared Python floor must not admit interpreters on which the pinned lib50 cannot import."""
    from importlib.metadata import metadata
    from packaging.specifiers import SpecifierSet

    setup_src = open("setup.py").read()
    ours = SpecifierSet(re.search(r'python_requires="([^"]+)"', setup_src).group(1))
    theirs = SpecifierSet(metadata("lib50")["Requires-Python"])
    for minor in range(6, 20):
        candidate = f"3.{minor}"
        assert not (candidate in ours and candidate not in theirs), (
            f"setup.py admits Python {candidate} but the installed lib50 requires {theirs}"
        )


# --- check_version / check_announcements ---

class FakeResponse:
    def __init__(self, status_code=200, text="", json_data=None):
        self.status_code = status_code
        self.text = text
        self._json_data = json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")

    def json(self):
        if self._json_data is None:
            raise requests.JSONDecodeError("not json", self.text, 0)
        return self._json_data


PYPI_OK = FakeResponse(json_data={"releases": {"3.0.0": [], "3.2.2": []}})
PYPI_NEWER = FakeResponse(json_data={"releases": {"3.0.0": [], "3.2.2": [], "9.9.9": []}})


def _fake_network(monkeypatch, io, pypi=PYPI_OK, local_version="3.2.2"):
    """Route requests.get to canned responses; an Exception value is raised instead."""
    def fake_get(url, **kwargs):
        resp = io if url.startswith(cli.SUBMIT_URL) else pypi
        if isinstance(resp, Exception):
            raise resp
        return resp

    monkeypatch.setattr(cli.requests, "get", fake_get)
    monkeypatch.setattr(cli, "__version__", local_version)


def test_check_version_up_to_date_is_silent(monkeypatch, capsys):
    _fake_network(monkeypatch, io=FakeResponse(text="3.0.0"))
    cli.check_version()
    assert capsys.readouterr().out == ""


def test_check_version_blocks_when_server_says_too_old(monkeypatch):
    _fake_network(monkeypatch, io=FakeResponse(text="9.9.9"))
    with pytest.raises(cli.Error, match="no longer supported"):
        cli.check_version()


def test_check_version_nudges_when_pypi_has_newer(monkeypatch, capsys):
    _fake_network(monkeypatch, io=FakeResponse(text="3.0.0"), pypi=PYPI_NEWER)
    cli.check_version()
    assert "newer version of submit50 is available" in capsys.readouterr().out


@pytest.mark.parametrize(
    "io",
    [
        pytest.param(requests.ConnectionError("dns"), id="offline"),
        pytest.param(requests.ReadTimeout("timeout"), id="timeout"),
        pytest.param(FakeResponse(status_code=503), id="outage"),
        pytest.param(FakeResponse(text="<html>maintenance</html>"), id="garbage body"),
    ],
)
def test_check_version_warns_but_proceeds_when_submit_io_unavailable(io, monkeypatch, capsys):
    _fake_network(monkeypatch, io=io)
    cli.check_version()
    assert "Could not check whether submit50 is up to date" in capsys.readouterr().out


@pytest.mark.parametrize(
    "pypi",
    [
        pytest.param(requests.ConnectionError("firewalled"), id="blocked"),
        pytest.param(requests.ReadTimeout("timeout"), id="timeout"),
        pytest.param(FakeResponse(status_code=503, text="<html>"), id="outage"),
        pytest.param(FakeResponse(json_data={"info": {}}), id="missing releases"),
    ],
)
def test_check_version_ignores_pypi_failures(pypi, monkeypatch, capsys):
    _fake_network(monkeypatch, io=FakeResponse(text="3.0.0"), pypi=pypi)
    cli.check_version()
    assert capsys.readouterr().out == ""


def test_check_version_skipped_when_not_installed_as_package(monkeypatch, capsys):
    """__init__ falls back to __version__ = "UNKNOWN" when package metadata is missing."""
    _fake_network(monkeypatch, io=FakeResponse(text="3.0.0"), local_version="UNKNOWN")
    cli.check_version()
    assert capsys.readouterr().out == ""


def test_check_announcements_blocks_on_announcement(monkeypatch):
    _fake_network(monkeypatch, io=FakeResponse(text="submit50 is down for maintenance"))
    with pytest.raises(cli.Error, match="down for maintenance"):
        cli.check_announcements()


@pytest.mark.parametrize(
    "io",
    [
        pytest.param(requests.ConnectionError("dns"), id="offline"),
        pytest.param(requests.ReadTimeout("timeout"), id="timeout"),
        pytest.param(FakeResponse(status_code=503), id="outage"),
    ],
)
def test_check_announcements_proceeds_when_unreachable(io, monkeypatch):
    _fake_network(monkeypatch, io=io)
    cli.check_announcements()


def test_version_output_shape():
    """The release workflow extracts the tag with `cut -d' ' -f2`; keep `<prog> <version>`."""
    out = subprocess.run(
        [sys.executable, "-m", "submit50", "--version"], capture_output=True, text=True, check=True
    ).stdout.strip()
    assert re.fullmatch(r"submit50 \d+\.\d+\.\d+", out), out
