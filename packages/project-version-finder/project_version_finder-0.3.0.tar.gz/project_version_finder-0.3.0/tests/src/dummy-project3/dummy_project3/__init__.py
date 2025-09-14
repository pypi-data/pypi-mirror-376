#!/usr/bin/env python
from project_version_finder import get_version  # type: ignore[import]


class Project3:
    pass


def fn():
    pass


__version__ = get_version("dummy-project3", fn.__globals__["__file__"])


__all__ = ["Project3", "__version__"]
