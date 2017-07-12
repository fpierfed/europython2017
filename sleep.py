#!/usr/bin/env python
"""
Just a simple replacement for the UNIX sleep tool for systems that do not have
that utility.
"""
import sys
import time


try:
    n = int(sys.argv[1])
except:
    sys.stderr.write('usage: sleep seconds\n')
    sys.exit(1)
time.sleep(n)
