import os
import sys

BUF_SIZE = 4096

while True:
    data = sys.stdin.buffer.read(BUF_SIZE)
    if not data:
        break
    if data == b"ab":
        print("python: crash!", file=sys.stderr)
        os.abort()
