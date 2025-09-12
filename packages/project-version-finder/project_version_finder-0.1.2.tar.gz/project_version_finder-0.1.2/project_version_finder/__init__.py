#! /usr/bin/env python
from sys import version_info, stderr
from tomlkit import api as toml_api
from typing import Union
from pathlib import Path

if version_info >= (3, 11):
    from importlib.metadata import version as metadata_version  # type: ignore[import,unused-ignore]
    from importlib.metadata import PackageNotFoundError
else:
    try:
        from importlib_metadata import version as metadata_version  # type: ignore[import,unused-ignore,no-redef]
        from importlib_metadata import PackageNotFoundError  # type: ignore[no-redef]
    except ModuleNotFoundError as e:
        raise ImportError(
            f"Failed to import project-version-finder, because version finder could load importlib.metadata.version: {str(e)}"
        )


def get_pyproject(
    directory: Union[Path, str, None] = None,
) -> Union[Path, None]:
    if directory == None:
        d = Path().cwd()
    elif isinstance(directory, Path):
        d = directory
    elif isinstance(directory, str):
        d = Path(directory)
    else:
        raise ValueError("get_pyproject requires either None (use CWD), a str, or a Path")
    d = d.expanduser().resolve()
    if not d.is_dir():
        raise ValueError("get_pyproject should be given the name of a directory")
    while d not in [
        Path(x)
        for x in [
            "/",
            "/home",
            "/var",
            "/tmp",
            "/usr",
        ]
    ]:
        if (d / "pyproject.toml").is_file():
            return d / "pyproject.toml"
        else:
            d = (d / "..").resolve()
    return None


def get_version(name: str, file_name: str) -> str:
    __version__: Union[str, None] = None
    directory = Path(file_name).parent

    fn = get_pyproject(directory)
    # if the project is installed, then the directory we find is
    # the installed version; so we can't find the pyproject.toml
    # file starting there. So, do the metadatta version first
    try:
        __version__ = str(metadata_version(name))
    except PackageNotFoundError as e:
        if not fn:
            raise FileNotFoundError(f"Unable to find pyproject.toml, and {name} is not installed")
        else:
            with open(fn, "r") as fp:
                try:
                    pyproject = toml_api.load(fp)
                except Exception as e:
                    raise ValueError(f'Found {fn}, but it is not a valid toml file: "{str(e)}"')
                try:
                    p_name = pyproject["project"]["name"]  # type: ignore[index]
                    p_version = str(pyproject["project"]["version"])  # type: ignore[index]
                except Exception as e:
                    raise ValueError(
                        f"Found {fn}, but it is not a valid pyproject.toml file: unable to project name an version"
                    )
                if p_name != name:
                    raise ValueError(
                        f"Found {fn}, but it is pyproject.toml for {p_name}, not {name}"
                    )
                else:
                    __version__ = p_version
    if not __version__:
        raise ValueError(f"Unable to determine version from metadata or pyproject.toml")
    return __version__


__version__ = get_version("project-version-finder", get_version.__globals__["__file__"])

__all__ = [
    # don't export __version__ by default, it might mess someone up
    "get_version",
]
