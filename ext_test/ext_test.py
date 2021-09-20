#!/opt/local/bin/python3.7

import sys
import re
import pathlib
import subprocess


MM_HASH_REGEX = r"^mm://(.+)$"


def log(obj):
    with open("/Users/matt/Repos/Mine/Experiments2/ext_test/out.log", "a+") as outfile:
        outfile.write(repr(obj) + "\n")


def main():
    log(sys.argv)
    filepath = sys.argv[1]
    log(filepath)

    if not filepath.endswith(".mm"):
        log("[-] Doesn't end with .mm")
        exit(1)

    filepath = pathlib.Path(filepath)
    target_parent_dir = filepath.parent
    target_dir = target_parent_dir / "mm-preview"

    with open(filepath, "r") as infile:
        match = re.match(MM_HASH_REGEX, infile.read().strip())
        if not match:
            log("[-] Doesn't contain a MediaMan URI (mm://).")
            exit(1)
        mm_hash = match.group(1)

    log(mm_hash)
    subprocess.call([
        "/Users/matt/Repos/Mine/Experiments2/ext_test/ext_hash_handler",
        target_dir,
        mm_hash,
    ])


if __name__ == '__main__':
    main()
