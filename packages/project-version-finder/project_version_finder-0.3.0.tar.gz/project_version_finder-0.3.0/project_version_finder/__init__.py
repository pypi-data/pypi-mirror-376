from .finder import get_version, get_pyproject

__version__ = get_version("project-version-finder")

__all__ = [
    # don't export __version__ by default, it might mess someone up
    "get_version",
]
