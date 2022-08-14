
import abc
import errno
import os
import tempfile
import typing

from FUSE.backends import mmbackend, osbackend
from FUSE.errors import readonly, deny, notreal
from FUSE.fuse_clients.abstract import AbstractReadOnlyFuseClient


FAKE_FILE_DESCRIPTOR = 0
FAKE_FOLDER_SIZE = 96
READ_ONLY_FOLDER_MODE = 0o40444
READ_ONLY_FILE_MODE = 0o100444

QUICKLOOK_PROCESSES = {
    "QuickLookSatellite",
    "QuickLookUIService",
    "quicklookd",
}


# TODO: satisfy the interface of AbstractReadOnlyFuseClient
class StubBackend:
    def has(self, path):
        return path in ("/", "/fake.txt")

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


# TODO: satisfy the interface of AbstractReadOnlyFuseClient
class StaticFlatBackend:
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


class ReadOnlyPassthrough(AbstractReadOnlyFuseClient):
    def __init__(self, root=None, mediaman=False, filesystem_image_mm_hash=None):
        if root:
            self.backend = osbackend.ReadOnlyOSBackend(root)
        elif mediaman:
            self.backend = mmbackend.ReadOnlyFlatMMBackend()
        elif filesystem_image_mm_hash:
            self.backend = mmbackend.ReadOnlyPredefinedMMBackend(filesystem_image_mm_hash=filesystem_image_mm_hash)
        else:
            self.backend = StaticFlatBackend({"a.txt": b"hi", "b.txt": b"ho!", "c.txt": b"how do you do?"})

    def verify_procname(self, procname):
        pass
        # if procname in QUICKLOOK_PROCESSES:
        #     deny()

    def access(self, path, mode):
        if not self.backend.has(path):
            notreal()

    def getattr(self, path, fh=None):
        if not self.backend.has(path):
            notreal()
        if self.backend.is_dir(path):
            return {
                "st_atime": 0,
                "st_ctime": 0,
                "st_mtime": 0,
                "st_nlink": 1,
                "st_uid": 0,  # orig 501
                "st_gid": 0,  # orig 20
                "st_mode": READ_ONLY_FOLDER_MODE,
                "st_size": FAKE_FOLDER_SIZE,
            }
        else:
            return {
                "st_atime": 0,
                "st_ctime": 0,
                "st_mtime": 0,
                "st_nlink": 1,  # 1 hard link
                "st_uid": 0,
                "st_gid": 0,
                "st_mode": READ_ONLY_FILE_MODE,
                "st_size": self.backend.size(path),
            }

    def readdir(self, path, fh):
        if not self.backend.has(path):
            notreal()
        dirents = [".", ".."]
        return dirents + self.backend.list(path)

    def readlink(self, path):
        deny()

    def statfs(self, path):
        stv = os.statvfs(path)
        out = dict((key, getattr(stv, key)) for key in (
            "f_bavail", "f_bfree", "f_blocks", "f_bsize",
            "f_favail", "f_ffree", "f_files", "f_flag",
            "f_frsize", "f_namemax"))
        out["f_flag"] |= os.ST_RDONLY  # read-only
        # out["f_frsize"] = 2**20
        return out

    def open(self, path, flags):
        if not self.backend.has(path):
            notreal()
        return FAKE_FILE_DESCRIPTOR

    def read(self, path, length, offset, fh):
        """
        NOTE: OS will try to read a file created via open().
        """
        print(path, length, offset)
        return self.backend.read(path, length, offset)

