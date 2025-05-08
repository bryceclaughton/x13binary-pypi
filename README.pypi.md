X13-ARIMA-SEATS PyPI distribution
=================================

The US Census Bureau provides a seasonal adjustment program now called 'X-13ARIMA-SEATS' building on both earlier programs called X-11 and X-12 as well as the SEATS program by the Bank of Spain.

Rationale
---------

X13-ARIMA-SEATS remains a critical tool in macroeconomic workflows, however it is not easily positioned to work in deployable environments.
This package aims to provide a binary that is callable by Python, or more simply, installs into the Python environment's scripts directory.

Usage
-----

To run X13-ARIMA-SEATS from the command line, use:

```shell
python -m x13binary
```

To run X13-ARIMA-SEATS from a Python program, you can use two methods.

```python
import sys, subprocess

subprocess.call([sys.executable, "-m", "x13binary"])
```

or

```python
import x13binary
import subprocess

subprocess.call([x13binary.find_x13_bin()])
```
