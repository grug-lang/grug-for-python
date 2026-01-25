import os
import sys

data = sys.stdin.buffer.read().decode()

if data == "ab":
    print("python: crash!", file=sys.stderr)
    os.abort()
