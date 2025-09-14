Project-Version-Finder

Simple package to provide version informaion. The stratagy is  
* first look in pyproject.toml, if it is found. This is most accurate during develompent, but when running from an install it probably will not be found, so  
* second, use importlib.metadata (or importlib_metadata, if appropriate), which works if it is installed.  

All you should need is  
```py
from project_version_finder import get_version
__version__ = get_version('project-name')
```
(and make project-version-finder a dependancy of your project).

If you do not want the search for pyproject.toml to start in the current working directory (which is often where you will automatically find your project in development in the python path), you can add a second argument specifying a file in the directory you wish to begin the search. Some suggestions (which may require all version tests during development to NOT have an installed version also available) are:
```py
from project_version_finder import get_version
# start search in directory of the file that defines __version__
__version__ = get_version('project-name', __file__)
```
or
```py
from project_version_finder import get_version
# start search in directory of the file that defines some function fn
__version__ = get_version('project-name', fn.__globals__['__file__'])
```

The key is to have a way to get the name of a file in the directory from which you wish the search to start. Bonus points if (like the default current working directory) this name will not follow the install files: then the result will work during development even if you have an older version installed.

It isn't fool proof, but since you provide the project name, if it finds the wrong pyproject.toml it should only fail if that happens to be for a different project with the same name.

[Repository](https://codeberg.org/Pusher2531/project-version-finder.git)  
[PyPI](https://pypi.org/project/project-version-finder/)  
