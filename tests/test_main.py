import os
import sys
import types

import pytest
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import lib50  # noqa: F401
except ImportError:  # e.g. Windows has no termios, which lib50 requires
    lib50 = types.ModuleType("lib50")
    config_mod = types.ModuleType("lib50.config")

    class Loader:
        def __init__(self, *args, **kwargs):
            pass

        def scope(self, *args, **kwargs):
            pass

    config_mod.Loader = Loader
    lib50.config = config_mod
    sys.modules["lib50"] = lib50

from submit50.__main__ import check_announcements


def test_check_announcements_uses_timeout(monkeypatch):
    """The status request must not be able to hang forever (no timeout)."""
    calls = {}

    class Resp:
        status_code = 404
        text = ""

    def fake_get(url, **kwargs):
        calls.update(kwargs)
        return Resp()

    monkeypatch.setattr(requests, "get", fake_get)
    check_announcements()
    assert calls.get("timeout") == 5
