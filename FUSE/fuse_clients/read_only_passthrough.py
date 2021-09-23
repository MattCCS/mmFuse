
import abc
import errno
import os
import tempfile
import typing


FAKE_FILE_DESCRIPTOR = 0
FAKE_FOLDER_SIZE = 96
READ_ONLY_FOLDER_MODE = 0o40444
READ_ONLY_FILE_MODE = 0o100444


def readonly():
    raise Exception(errno.EROFS)

def deny():
    raise Exception(errno.EACCES)

def notreal():
    raise Exception(errno.ENOENT)


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


class StaticFlatBackend:
    def __init__(self, files):
        self._files = dict(files)

    def has(self, path):
        path = path.lstrip("/")
        return path == "" or path in self._files

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


class AbstractReadOnlyPassthrough(abc.ABC):

    @abc.abstractmethod
    def verify_procname(self, procname):      raise NotImplementedError()  # noqa

    @abc.abstractmethod
    def access(self, path, mode):             raise NotImplementedError()  # noqa

    @abc.abstractmethod
    def getattr(self, path, fh=None):         raise NotImplementedError()  # noqa

    @abc.abstractmethod
    def readdir(self, path, fh):              raise NotImplementedError()  # noqa

    @abc.abstractmethod
    def readlink(self, path):                 raise NotImplementedError()  # noqa

    @abc.abstractmethod
    def statfs(self, path):                   raise NotImplementedError()  # noqa

    @abc.abstractmethod
    def open(self, path, flags):              raise NotImplementedError()  # noqa

    @abc.abstractmethod
    def read(self, path, length, offset, fh): raise NotImplementedError()  # noqa

    def destroy(self, path):
        readonly()

    def chmod(self, path, mode):
        readonly()

    def chown(self, path, uid, gid):
        readonly()

    def mknod(self, path, mode, dev):
        readonly()

    def rmdir(self, path):
        readonly()

    def mkdir(self, path, mode):
        readonly()

    def unlink(self, path):
        readonly()

    def symlink(self, target, name):
        readonly()

    def rename(self, old, new):
        readonly()

    def link(self, target, name):
        readonly()

    def utimens(self, path, times=None):
        readonly()

    def create(self, path, mode, fi=None):
        readonly()

    def write(self, path, buf, offset, fh):
        readonly()

    def truncate(self, path, length, fh=None):
        readonly()

    def flush(self, path, fh):
        """
        NOTE: OS will call [open > flush > release] even to read a file.
        """
        pass

    def release(self, path, fh):
        """
        NOTE: OS will call [open > flush > release] even to read a file.
        """
        pass

    def fsync(self, path, fdatasync, fh):
        readonly()


class ReadOnlyPassthrough(AbstractReadOnlyPassthrough):
    def __init__(self, root):
        self.root = root
        self.backend = StaticFlatBackend({"a.txt": b"hi", "b.txt": b"ho!", "c.txt": b"how do you do?"})

    def verify_procname(self, procname):
        pass

    def access(self, path, mode):
        if not self.backend.has(path):
            notreal()

    def getattr(self, path, fh=None):
        if path == "/":
            return {
                'st_atime': 0,
                'st_ctime': 0,
                'st_mtime': 0,
                'st_nlink': 1,
                'st_uid': 0,  # orig 501
                'st_gid': 0,  # orig 20
                'st_mode': READ_ONLY_FOLDER_MODE,
                'st_size': FAKE_FOLDER_SIZE,
            }
        elif self.backend.has(path):
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
        notreal()

    def readdir(self, path, fh):
        if not self.backend.has(path):
            notreal()
        dirents = ['.', '..']
        return dirents + self.backend.list(path)

    def readlink(self, path):
        deny()

    def statfs(self, path):
        stv = os.statvfs(path)
        out = dict((key, getattr(stv, key)) for key in (
            'f_bavail', 'f_bfree', 'f_blocks', 'f_bsize',
            'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))
        out["f_flag"] |= os.ST_RDONLY  # read-only
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

