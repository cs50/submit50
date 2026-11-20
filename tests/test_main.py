"""Tests for the preflight checks submit50 runs against submit.cs50.io and PyPI."""
import pytest
import requests

import submit50.__main__ as cli


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
