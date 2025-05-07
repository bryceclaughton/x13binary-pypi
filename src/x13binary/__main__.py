from __future__ import annotations

import os
import sys
from x13binary import find_x13_bin


if __name__ == "__main__":
    x13 = os.fsdecode(find_x13_bin())
    if sys.platform == "win32":
        import subprocess

        completed_process = subprocess.run([x13, *sys.argv[1:]])
        sys.exit(completed_process.returncode)
    else:
        os.execvp(x13, [x13, *sys.argv[1:]])
