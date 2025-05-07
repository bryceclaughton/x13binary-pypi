X13-ARIMA-SEATS PyPI distribution
=================================

This repository contains the scripts used to package the [binary releases][x13dl] of the [X13-ARIMA-SEATS package][x13].
This document is meant for maintainers.

The repackaged artifacts are published as the [x13binary PyPI package][pypi]

[x13]: https://www.census.gov/data/software/x13as.About_X-13.html
[x13dl]: https://www.census.gov/data/software/x13as.X-13ARIMA-SEATS.html
[pypi]: https://pypi.org/project/x13binary/

How-to
------

The script requires Python 3.10 or later as well as a [PEP 723][pep723] compatible script runner, such as [`uv`][uv].

[pep723]: https://peps.python.org/pep-0723/
[uv]: https://docs.astral.sh/uv/#script-support/

Building wheels
---------------

Run the `make_wheels.py` script.

```shell
uv run make_wheels.py
```

Thank you
---------

Thanks to the US Census Bureau for providing inspiration for this with their [`x13binary`][x13binary] package for R.
Thanks to the [Zig team][zigpypi] for providing 95% of the code to create this project.

[x13binary]: https://github.com/x13org/x13binary/
[zigpypi]: https://github.com/ziglang/zig-pypi/
