#!/usr/bin/env python
# since we are testing, project_version_finder isn't installed when I run mypy
from project_version_finder import get_version  # type: ignore[import]


class Project4:
    pass


def fn():
    pass


__version__ = get_version("dummy-project7", fn.__globals__["__file__"])  # yes, that's wrong


__all__ = ["Project4", "__version__"]
