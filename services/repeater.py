#!/usr/bin/python

import time
import os
import sys
import random
import subprocess

if __name__ == '__main__':
    fnull = open(os.devnull, "w")
    while True:
        time.sleep(random.randint(1, 3))
        subprocess.call(sys.argv[1:], stdout=fnull, stderr=fnull)
        time.sleep(random.randint(1, 7))
