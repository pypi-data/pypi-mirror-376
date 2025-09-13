Project-Version-Finder

Simple package to provide version informaion. The stratagy is  
* first, use importlib.metadata (or importlib_metadata, if appropriate), which works if it is installed.  
* second look in pyproject.toml  

All you should need is  
```py
from project_version_finder import get_version
nn
fn dummy():
    pass
	
__version__ = get_version('project-name', dummy.__globals__['__file__'])
```
(and make project-version-finder a dependancy of your project). The second argment to get_version is the path (as a string) to some file in your package directory. One way to get that path without hard coding it is by getting it from a function defined in your `__init__.py` file, or, as shown here, by defining a dummy function for that purpose.

It isn't fool proof, but since you provide the project name, if it finds the wrong pyproject.toml it should only fail if that happens to be for a different project with the same name.

[Repository](https://codeberg.org/Pusher2531/project-version-finder.git)  
[PyPI](https://pypi.org/project/project-version-finder/)  

