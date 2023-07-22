
import argparse
import collections
import json
import pathlib

import xxhash


def xxh64(path, buffer=1024**2):
    """
    Hashes the contents of the given filepath in chunks.
    Returns a hex digest (0-9a-f) of the xxh64 hash.
    Performance on a Macbook Pro is about 4.20 GB/s.
    """
    import xxhash
    import sys

    xxh64 = xxhash.xxh64(seed=0)
    read = 0

    with open(path, "rb") as infile:
        data = infile.read(buffer)
        read += buffer
        while data:
            xxh64.update(data)
            data = infile.read(buffer)
            read += buffer

    return f"xxh64:{xxh64.hexdigest()}"


def get_hash(path):
    # TODO(mcotton): try to read xargs?
    return xxh64(path)


def path_to_keys(path):
    path = str(path)
    if not path or path == "/":
        return []
    return path.lstrip("/").split("/")


def set_nested(tree, keys, value):
    (*path, last) = keys
    for k in path:
        tree = tree[k]
    tree[last] = value


def form_directory_tree(path):
    print(f"mapping {path}")
    tree_factory = lambda: collections.defaultdict(tree_factory)
    tree = tree_factory()

    g = path.rglob("*")
    for p in g:
        relative_path = p.relative_to(path)
        keys = path_to_keys(relative_path)
        print(f"adding {relative_path}{'/' if p.is_dir() else ''}")

        if p.is_file():
            entry = {
                "file": True,
                "hash": get_hash(p),
                "size": p.stat().st_size,
            }
        else:
            entry = {}

        set_nested(tree, keys, entry)

    return tree


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    return parser.parse_args()


def main():
    args = parse_args()
    tree = form_directory_tree(pathlib.Path(args.path))
    print(json.dumps(tree, indent=4))


if __name__ == '__main__':
    main()

