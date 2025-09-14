#!/usr/bin/env python
from project_version_finder import get_version  # type: ignore[import]


class Project1:
    pass


__version__ = get_version("dummy-project1")


__all__ = ["Project1", "__version__"]
