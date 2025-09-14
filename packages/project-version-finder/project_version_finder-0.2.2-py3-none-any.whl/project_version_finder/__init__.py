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
        if version_info >= (3, 11):
            raise ImportError(
                f"Failed to import project-version-finder, because version finder could load importlib.metadata.version: {str(e)}"
            )
        else:
            raise ImportError(
                f"Failed to import project-version-finder, because version finder could load importlib_metadata.version: {str(e)}"
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
    # print(f"Search starting at {d}")
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
            # print(f"found {d / 'pyproject.toml'}")
            return d / "pyproject.toml"
        else:
            # print(f"no pyproject.toml in {d}, search {d / '..'}")
            d = (d / "..").resolve()
    return None


def get_version(name: str, file_name: Union[str, None] = None) -> str:
    __version__: Union[str, None] = None
    if file_name:
        directory: Union[Path, None] = Path(file_name).parent
    else:
        directory = None
    fn = get_pyproject(directory)
    failure: str = ""
    if not fn:
        failure = f"unable to find pyproject.toml"
    else:
        with open(fn, "r") as fp:
            try:
                pyproject = toml_api.load(fp)
            except Exception as e:
                failure = f'found {fn}, but it is not a valid toml file: "{str(e)}"'
            try:
                p_name = pyproject["project"]["name"]  # type: ignore[index]
                p_version = str(pyproject["project"]["version"])  # type: ignore[index]
            except Exception as e:
                failure = f"found {fn}, but it is not a valid pyproject.toml file: unable to project name an version"
            if p_name != name:
                failure = f"found {fn}, but it is pyproject.toml for {p_name}, not {name}"
            else:
                __version__ = p_version
    if not __version__:
        try:
            __version__ = str(metadata_version(name))
        except PackageNotFoundError as e:
            reason = (
                f"Unable to get __version__ of {name} from install metadata({str(e)}) and {failure}"
            )
            if failure[: len("found ")] == "found ":
                raise ValueError(reason)
            else:
                raise FileNotFoundError(reason)
    return __version__


__version__ = get_version("project-version-finder", get_version.__globals__["__file__"])

__all__ = [
    # don't export __version__ by default, it might mess someone up
    "get_version",
]
