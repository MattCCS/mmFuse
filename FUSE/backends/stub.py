
from FUSE.backends.abstract import AbstractReadOnlyBackend
from FUSE.errors import deny, notreal


class StubBackend(AbstractReadOnlyBackend):
    def has(self, path):
        return path in ("/", "/fake.txt")

    def is_dir(self, path):
        return path == "/"

    def list(self, path):
        if path == "/":
            return ["fake.txt"]
        deny()

    def size(self, path):
        if path == "fake.txt":
            return 100
        notreal()

    def read(self, path, length, offset):
        if path == "fake.txt":
            return (b"X" * 100)[offset:][:length]
        notreal()
