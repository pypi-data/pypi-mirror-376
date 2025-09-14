#! /usr/bin/env python
from .finder import get_version
from sys import argv, stderr

def version_finder() -> None:
    if len(argv) < 2 or argv[1] == '-h' or argv[1] == '--help' :
        print(f"Usage: version_finder 'name-of-package'")
        return
    else:
        print(get_version(argv[1]))
        return

if __name__ == '__main__' :
    version_finder()


