# PAQUO: PAthological QUpath Obsession

[![PyPI Version](https://img.shields.io/pypi/v/paquo)](https://pypi.org/project/paquo/)
[![Read the Docs](https://img.shields.io/readthedocs/paquo)](https://paquo.readthedocs.io)
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/bayer-science-for-a-better-life/paquo/paquo%20ci?label=tests)](https://github.com/bayer-science-for-a-better-life/paquo/actions)
[![Codecov](https://img.shields.io/codecov/c/github/bayer-science-for-a-better-life/paquo)](https://codecov.io/gh/bayer-science-for-a-better-life/paquo)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/paquo)](https://github.com/bayer-science-for-a-better-life/paquo)
[![GitHub issues](https://img.shields.io/github/issues/bayer-science-for-a-better-life/paquo)](https://github.com/bayer-science-for-a-better-life/paquo/issues)

Welcome to `paquo` :wave:, a library for interacting with [QuPath](https://qupath.github.io/)
from [Python](https://www.python.org/).

`paquo`'s goal is to provide a pythonic interface to important features of
QuPath, and to make creating and working with QuPath projects intuitive for
Python programmers.

We strive to make your lives as easy as possible: If `paquo` is not pythonic,
unintuitive, slow or if its documentation is confusing, it's a bug in
`paquo`. Feel free to report any issues or feature requests in the issue
tracker!

Development 
[happens on github](https://github.com/bayer-science-for-a-better-life/paquo)
:octocat:

## Documentation

You can find `paquo`'s documentation at
[paquo.readthedocs.io](https://paquo.readthedocs.io) :heart:


## Development Installation

1. Install conda and git
2. Clone paquo `git clone https://github.com/bayer-science-for-a-better-life/paquo.git`
3. Run `conda env create -f environment.yaml`
4. Activate the environment `conda activate paquo`

Note that in this environment `paquo` is already installed in development mode,
so go ahead and hack.


## Contributing Guidelines

- Please follow [pep-8 conventions](https://www.python.org/dev/peps/pep-0008/) but:
  - We allow 120 character long lines (try anyway to keep them short)
- Please use [numpy docstrings](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard).
- When contributing code, please try to use Pull Requests.
- tests go hand in hand with modules on ```tests``` packages at the same level. We use ```pytest```.

You can setup your IDE to help you adhering to these guidelines.
<br>
_([Santi](https://github.com/sdvillal) is happy to help you setting up pycharm in 5 minutes)_


## Acknowledgements

Build with love by Andreas Poehlmann and Santi Villalba from the _Machine
Learning Research_ group at Bayer. In collaboration with the _Pathology Lab 2_
and the _Mechanistic and Toxicologic Pathology_ group.

`paquo`: copyright 2020 Bayer AG, licensed under [GPL-3.0](https://github.com/bayer-science-for-a-better-life/paquo/blob/master/LICENSE)
