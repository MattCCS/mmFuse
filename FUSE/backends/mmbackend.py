
import errno
import functools
import json
import os
import pathlib
import sys

sys.path.append(os.environ.get("MMSRC", ""))
import mediaman.core.api

from FUSE.backends.abstract import AbstractReadOnlyBackend
from FUSE.caches import block_cache
from FUSE.errors import deny, notreal


class ReadOnlyPredefinedMMBackend(AbstractReadOnlyBackend):
    def __init__(self, filesystem_image_mm_hash="xxh64:28958e05597643fb", service_selector="local"):
        self._service_selector = service_selector

        result = mediaman.core.api.run_stream(
            root=pathlib.Path(),
            file_name=filesystem_image_mm_hash,
            service_selector=self._service_selector,
        )
        self._filesystem = json.loads(list(result)[0])
        self._caches = {}  # hash -> func()

        print("ready")

    @staticmethod
    def _path_to_keys(path):
        if path == "/":
            return []
        return path.lstrip("/").split("/")

    @staticmethod
    def _is_dir(obj):
        return isinstance(obj, dict) and obj.get("file", False) is False

    def _access(self, path):
        keys = ReadOnlyPredefinedMMBackend._path_to_keys(path)
        print(f"_access ({path=}) - {keys=}")
        d = self._filesystem
        try:
            for k in keys:
                d = d[k]
        except KeyError:
            return None
        return d

    def has(self, path):
        print(f"has ({path})")
        return self._access(path) is not None

    def is_dir(self, path):
        print(f"is_dir ({path})")
        return ReadOnlyPredefinedMMBackend._is_dir(self._access(path))

    def list(self, path):
        print(f"list ({path})")
        obj = self._access(path)
        if obj is None:
            deny()
        return list(obj.keys())

    def size(self, path):
        print(f"size ({path})")
        obj = self._access(path)
        if obj is None:
            notreal()
        elif self._is_dir(obj):
            return 0  # TODO(mcotton): what should dir size be?
        return obj["size"]

    def read(self, path, length, offset):
        print(f"read ({path=}, {length=}, {offset=})")
        obj = self._access(path)
        if obj is None:
            notreal()
        elif self._is_dir(obj):
            deny()
        hash = obj["hash"]

        if hash not in self._caches:
            self._caches[hash] = block_cache.BlockwiseBuffer(
                size=obj["size"],
                source=functools.partial(self._read, hash),
            )
        buffer = self._caches[hash]

        return buffer.read(length=length, offset=offset)

    def _read(self, hash, length, offset):
        print(f"_read ({hash}, {length}, {offset})")
        try:
            return b"".join(mediaman.core.api.run_stream_range(
                service_selector=self._service_selector,
                root=pathlib.Path(),
                file_name=hash,
                offset=offset,
                length=length,
            ))
        except TypeError:
            raise notreal()


class ReadOnlyFlatMMBackend(AbstractReadOnlyBackend):
    def __init__(self, service_selector="local"):
        service_selector = "sam"
        self._service_selector = service_selector
        print(service_selector)

        # full list:
        # self._list_result = mediaman.core.api.run_list(service_selector=self._service_selector)

        # search test:
        self._list_result = list(mediaman.core.api.run_fuzzy("png", service_selector=self._service_selector))[0][1]

        self._files = {
            f["name"] : {
                "size": f["size"],
                "hash": f["hashes"][0],
                "buffer": block_cache.BlockwiseBuffer(
                    size=f["size"],
                    source=functools.partial(self._read, f["hashes"][0]),
                )
            }
            for f in self._list_result
        }
        print("ready")

    def has(self, path):
        path = path.lstrip("/")
        return path == "" or path in self._files

    def is_dir(self, path):
        print(f"is_dir ({path})")
        return path == "/"

    def list(self, path):
        print(f"list ({path})")
        path = path.lstrip("/")
        if path == "":
            return list(self._files.keys())
        deny()

    def size(self, path):
        path = path.lstrip("/")
        if path in self._files:
            return self._files[path]["size"]
        notreal()

    def read(self, path, length, offset):
        path = path.lstrip("/")
        if path in self._files:
            ref = self._files[path]["buffer"]
            return ref.read(offset=offset, length=length)
        notreal()

    def _read(self, hash, length, offset):
        print(f"_read ({hash}, {length}, {offset})")
        return b"".join(mediaman.core.api.run_stream_range(
            service_selector=self._service_selector,
            root=pathlib.Path(),
            file_name=hash,
            offset=offset,
            length=length,
        ))


def test():
    b = ReadOnlyPredefinedMMBackend()
    print(b)

if __name__ == '__main__':
    test()
