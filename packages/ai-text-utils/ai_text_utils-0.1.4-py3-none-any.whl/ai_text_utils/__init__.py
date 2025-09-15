import tomllib
from pathlib import Path

def get_version():
    """Read version from pyproject.toml"""
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    try:
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)
        return pyproject["project"]["version"]
    except (FileNotFoundError, KeyError):
        return "unknown"

__version__ = get_version()