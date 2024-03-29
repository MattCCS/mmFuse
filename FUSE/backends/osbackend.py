
import errno
import functools
import os
import pathlib

from FUSE.backends.abstract import AbstractReadOnlyBackend
from FUSE.caches import block_cache
from FUSE.errors import notreal


class ReadOnlyOSBackend(AbstractReadOnlyBackend):
    def __init__(self, root):
        self._root = pathlib.Path(root)
        self._files = {}

        if not self._root.exists():
            print(self._root.absolute())
            raise RuntimeError(f"Root path ({root}) is not real!")

        for p in self._root.glob("**/*"):
            if not (p.is_file() or p.is_dir()):
                continue

            path = "/" + str(p.relative_to(self._root))
            realpath = str(p)
            type = "file" if p.is_file() else "dir"
            size = p.stat().st_size
            self._files[path] = {
                "type": type,
                "size": size,
                "buffer": block_cache.BlockwiseBuffer(
                    size=size,
                    source=functools.partial(self._read, realpath)
                )
            }

        # print(self._files.keys())
        print(f"ready: ReadOnlyOSBackend({self._root})")

    def has(self, path):
        print(f"has {(path)}")
        out = path == "/" or path in self._files
        print(out); return out

    def is_dir(self, path):
        print(f"is_dir {(path)}")
        out = path == "/" or self._files[path]["type"] == "dir"
        print(out); return out

    def list(self, path):
        print(f"list {(path)}")
        out = [
            str(pathlib.Path(p).relative_to(path)).strip("/")
            for p in self._files
            if pathlib.PurePath(p).match(
                (path + "/*") if path.lstrip("/") else "/*"
            )
        ]
        print(out); return out

    def size(self, path):
        print(f"size {(path)}")
        # path = path.lstrip("/")
        if path in self._files:
            out = self._files[path]["size"]
            print(out); return out
        notreal()

    def read(self, path, length, offset):
        print(f"read {(path, length, offset)}")
        # path = path.lstrip("/")
        if path in self._files:
            ref = self._files[path]["buffer"]
            return ref.read(offset=offset, length=length)
        notreal()

    def _read(self, path, length, offset):
        with open(path, "r+b") as infile:
            infile.seek(offset)
            return infile.read(length)
