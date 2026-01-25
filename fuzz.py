import os
import sys

data = sys.stdin.buffer.read()

if data == b"ab":
    print("python: crash!", file=sys.stderr)
    os.abort()
