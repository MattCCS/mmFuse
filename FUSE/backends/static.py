
from FUSE.backends.abstract import AbstractReadOnlyBackend
from FUSE.errors import deny, notreal


class StaticFlatBackend(AbstractReadOnlyBackend):
    def __init__(self, files):
        self._files = dict(files)

    def has(self, path):
        path = path.lstrip("/")
        return path == "" or path in self._files

    def is_dir(self, path):
        return path == "/"

    def list(self, path):
        path = path.lstrip("/")
        if path == "":
            return list(self._files.keys())
        deny()

    def size(self, path):
        path = path.lstrip("/")
        if path in self._files:
            return len(self._files[path])
        notreal()

    def read(self, path, length, offset):
        path = path.lstrip("/")
        if path in self._files:
            return self._files[path][offset:][:length]
        notreal()
