#!/usr/bin/env python
from os import environ
from sys import path as python_path

python_path.insert(0, environ["PWD"])

if "EXPECT_VERSION" in environ:
    e_version = environ["EXPECT_VERSION"]
else:
    e_version = "1.2.3"

if "EXPECT_ERROR" in environ:
    e_error = environ["EXPECT_ERROR"]
else:
    e_error = ""

try:
    from dummy_project3 import __version__

    if __version__ == e_version:
        print("OK")
    else:
        print(f"FAIL: expecting {e_version}, got {__version__}")
except FileNotFoundError as e:
    error = str(e)
    if error == e_error:
        print("OK")
    else:
        print(f"FAIL: FileNotFound\n'{error}'\nbut expecting\n'{e_error}'")
except ValueError as e:
    error = str(e)
    if error == e_error:
        print("OK")
    else:
        print(f"FAIL: ValueError '{error}'")
