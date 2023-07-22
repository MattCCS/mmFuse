
import errno
import functools
import os
import pathlib
import sys

sys.path.append("/Users/matt/home/Repos/Mine/MediaMan/")
import mediaman.core.api

from FUSE.caches import cachetest2


def readonly():
    raise Exception(errno.EROFS)

def deny():
    raise Exception(errno.EACCES)

def notreal():
    raise Exception(errno.ENOENT)


# TODO: rename ReadOnlyFlatMMBackend
class FlatMMBackend:
    def __init__(self, service_selector="local", safe_limit=-1):
        self._service_selector = service_selector
        print(service_selector)
        self._list_result = mediaman.core.api.run_list(service_selector=self._service_selector)
        self._files = {
            f["name"] : {
                "size": f["size"],
                "hash": f["hashes"][0],
                "reader": cachetest2.BlockwiseBuffer(
                    size=f["size"],
                    source=functools.partial(self._read, f["hashes"][0])
                ).read
            }
            for f in list(self._list_result)[:safe_limit]
        }
        print("ready")

    def has(self, path):
        path = path.lstrip("/")
        return path == "" or path in self._files

    def is_dir(self, path):
        path = path.lstrip("/")
        return path == ""  # FlatMMBackend only has one dir (/)

    def list(self, path):
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
            reader = self._files[path]["reader"]
            return reader(offset=offset, length=length)
        notreal()

    def _read(self, hash, length, offset):
        return b"".join(mediaman.core.api.run_stream_range(
            service_selector=self._service_selector,
            root=pathlib.Path(),
            file_name=hash,
            offset=offset,
            length=length,
        ))
