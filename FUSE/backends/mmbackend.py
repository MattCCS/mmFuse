
import functools
import json
import logging
import os
import pathlib
import sys

sys.path.append(os.environ.get("MMSRC", ""))
from mediaman.core import policy

from FUSE.backends.abstract import AbstractReadOnlyBackend
from FUSE.caches import block_cache
from FUSE.errors import deny, notreal


(logger := logging.getLogger(__name__)).setLevel(logging.INFO)
logging.getLogger("mattccs.mediaman").setLevel(logging.INFO)


class ReadOnlyPredefinedMMBackend(AbstractReadOnlyBackend):
    def __init__(self, filesystem_image=None, filesystem_image_mm_hash="xxh64:28958e05597643fb", service_selector=None):
        self._service_selector = service_selector
        self._service = policy.load_client(service_selector=self._service_selector)

        if filesystem_image:
            self._filesystem = json.loads(filesystem_image)
        else:
            result = self._service.stream(
                root=pathlib.Path(),
                identifier=filesystem_image_mm_hash,
            )
            self._filesystem = json.loads(list(result)[0])
        self._caches = {}  # hash -> func()

        logging.info("ready")

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
        logging.debug(f"_access ({path=}) - {keys=}")
        d = self._filesystem
        try:
            for k in keys:
                d = d[k]
        except KeyError:
            return None
        return d

    def has(self, path):
        logging.debug(f"has ({path})")
        return self._access(path) is not None

    def is_dir(self, path):
        logging.debug(f"is_dir ({path})")
        return ReadOnlyPredefinedMMBackend._is_dir(self._access(path))

    def list(self, path):
        logging.debug(f"list ({path})")
        obj = self._access(path)
        if obj is None:
            deny()
        return list(obj.keys())

    def size(self, path):
        logging.debug(f"size ({path})")
        obj = self._access(path)
        if obj is None:
            notreal()
        elif self._is_dir(obj):
            return 0  # TODO(mcotton): what should dir size be?
        return obj["size"]

    def read(self, path, length, offset):
        logging.debug(f"read ({path=}, {length=}, {offset=})")
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
        logging.debug(f"_read ({hash}, {length}, {offset})")
        try:
            return b"".join(self._service.stream_range(
                root=pathlib.Path(),
                identifier=hash,
                offset=offset,
                length=length,
            ))
        except TypeError:
            raise notreal()


class ReadOnlyFlatMMBackend(AbstractReadOnlyBackend):
    def __init__(self, service_selector="local"):
        # service_selector = "sam"
        self._service_selector = service_selector
        logging.debug(f"{service_selector=}")
        self._service = policy.load_client(service_selector=None)

        # full list:
        # self._list_result = mediaman.core.api.run_list(service_selector=self._service_selector)

        # search test:
        self._list_result = list(self._service.fuzzy_search_by_name(""))[0][1]
        # self._list_result = list(self._service.list_files())

        self._files = {
            f["name"] : {
                "size": f["size"],
                "hash": f["hashes"][0],
                "buffer": block_cache.BlockwiseBuffer(
                    size=f["size"],
                    source=functools.partial(self._read, f["hashes"][0]),
                    prefetch_blocks=2,  # TODO(mcotton): Drive can't multithread
                )
            }
            for f in self._list_result
        }
        logging.debug("ready")

    def has(self, path):
        path = path.lstrip("/")
        return path == "" or path in self._files

    def is_dir(self, path):
        logging.debug(f"is_dir ({path})")
        return path == "/"

    def list(self, path):
        logging.debug(f"list ({path})")
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
        logging.debug(f"_read ({hash}, {length}, {offset})")
        return b"".join(self._service.stream_range(
            root=pathlib.Path(),
            identifier=hash,
            offset=offset,
            length=length,
        ))


def test():
    backend = ReadOnlyPredefinedMMBackend()
    logging.debug(f"{backend=}")

if __name__ == '__main__':
    test()
