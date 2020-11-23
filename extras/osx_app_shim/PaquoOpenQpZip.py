#!/usr/bin/env python

import sys
from paquo._cli import open_qupath

try:
    sys.exit(open_qupath(sys.argv[1]))
except BaseException:
    sys.exit(1)
