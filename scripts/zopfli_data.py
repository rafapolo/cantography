"""Recompress the site's gzip files with zopfli: same gzip format, so the browser's
DecompressionStream reads them as before, ~6% smaller than gzip -9.

Run it last, after the scripts that write data/ (they write plain gzip -9). A file
is only rewritten when zopfli beats it and its content comes back identical, so a
second run skips what is done.

    uv run --with zopfli python scripts/zopfli_data.py [files...]
"""
import gzip
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from glob import glob

import zopfli.gzip

# what the page fetches; registered.json.gz and opening_dates.json.gz are pipeline inputs
DEFAULT = glob("data/[A-Z][A-Z]_0.json.gz") + ["data/search_index.json.gz", "data/timeline/events.bin.gz"] + glob("data/timeline/names/*.json.gz")
ITERATIONS = 5


def squeeze(path):
    with open(path, "rb") as f:
        old = f.read()
    raw = gzip.decompress(old)
    new = zopfli.gzip.compress(raw, numiterations=ITERATIONS)
    if len(new) >= len(old) or gzip.decompress(new) != raw:
        return path, len(old), len(old)
    with open(path + ".tmp", "wb") as f:
        f.write(new)
    os.replace(path + ".tmp", path)
    return path, len(old), len(new)


def main():
    files = sorted(sys.argv[1:] or DEFAULT, key=os.path.getsize, reverse=True)
    before = after = 0
    with ProcessPoolExecutor() as pool:
        for path, a, b in pool.map(squeeze, files):
            before += a
            after += b
            print(f"{path}: {a:,} -> {b:,}", flush=True)
    print(f"[ZOPFLI] {len(files)} files  {before:,} -> {after:,} bytes  (-{(before - after) / max(before, 1):.1%})")


if __name__ == "__main__":
    main()
