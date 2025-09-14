#!/usr/bin/env python
from project_version_finder import get_version  # type: ignore[import]


class Project2:
    pass


__version__ = get_version("dummy-project2", __file__)


__all__ = ["Project2", "__version__"]
