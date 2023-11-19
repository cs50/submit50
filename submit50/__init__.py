from importlib.metadata import PackageNotFoundError, version
import os

try:
    __version__ = version("submit50")
except PackageNotFoundError:
    __version__ = "UNKNOWN"

CONFIG_LOADER = __import__("lib50").config.Loader("submit50")
CONFIG_LOADER.scope("files", "include", "exclude", "require")
