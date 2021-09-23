
import errno
import os
import pathlib
import tempfile
import typing


class TempItem:
    pass


class TempfileWrapper(TempItem):
    def __init__(self, dir):
        self.t = tempfile.NamedTemporaryFile(dir=dir)

    def name(self):
        return self.t.name

    def read(self, length, offset):
        self.t.seek(offset)
        return self.t.read(length)

    def write(self, data, offset):
        self.t.seek(offset)
        return self.t.write(data)

    def truncate(self, length):
        return self.t.truncate(length)

    def size(self, length):
        return self.t.seek(0, 2)  # whence=2

    def dump(self):
        # TODO: could use t.write(outbuf) instead
        self.t.seek(0)
        return self.t.read()


class TempdirWrapper(TempItem):
    def __init__(self, dir):
        self.t = tempfile.TemporaryDirectory(dir=dir)

    def name(self):
        return self.t.name


FAKE_FILE_DESCRIPTOR = -1  # TODO: Does this fake file descriptor work?


class TempfilePassthrough:
    def __init__(self, root):
        self.root = root
        self.items: typing.Dict[str, TempItem] = {
            self._full_path("/"): TempdirWrapper(None)
        }

        self.build(pathlib.Path(root), self.items)
        print(self.items)

    def build(self, path, items):
        for i in path.iterdir():
            print(path, i)
            if i.is_file():
                items[i.absolute()] = TempfileWrapper(dir=items[str(path)].name())
            elif i.is_dir():
                items[i.absolute()] = TempdirWrapper(dir=items[str(path)].name())
                self.build(i, items)

    def verify_procname(self, procname):
        pass

    def destroy(self, path):
        pass

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial).rstrip("/")
        return path

    def _at(self, path):
        fp = self._full_path(path)
        print(fp)
        try:
            return self.items[fp].name()
        except KeyError:
            raise Exception(errno.ENOENT)

    def access(self, path, mode):
        if not os.access(self._at(path), mode):
            raise Exception(errno.EACCES)

    def chmod(self, path, mode):
        return os.chmod(self._at(path), mode)

    def chown(self, path, uid, gid):
        return os.chown(self._at(path), uid, gid)

    def getattr(self, path, fh=None):
        st = os.lstat(self._at(path))
        return dict((key, getattr(st, key)) for key in (
            'st_atime', 'st_ctime', 'st_gid', 'st_mode',
            'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

    def readdir(self, path, fh):
        full_path = self._full_path(path)

        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        return list(dirents)

    def readlink(self, path):
        return path
        # pathname = os.readlink(self._full_path(path))
        # if pathname.startswith("/"):
        #     # Path name is absolute, sanitize it.
        #     return os.path.relpath(pathname, self.root)
        # else:
        #     return pathname

    def mknod(self, path, mode, dev):
        pass
        # return os.mknod(self._full_path(path), mode, dev)

    def rmdir(self, path):
        return os.rmdir(self._at(path))

    def mkdir(self, path, mode):
        full_path = self._full_path(path)
        if full_path in self.items:
            raise Exception(errno.EEXIST)
        self.items[full_path] = TempdirWrapper()  # TODO: needs to be under dir

    def statfs(self, path):
        print(path)
        print(self._at(path))
        stv = os.statvfs(self._at(path))
        return dict((key, getattr(stv, key)) for key in (
            'f_bavail', 'f_bfree', 'f_blocks', 'f_bsize',
            'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def unlink(self, path):
        pass
        # return os.unlink(self._full_path(path))

    def symlink(self, target, name):
        pass
        # return os.symlink(self._full_path(target), self._full_path(name))

    def rename(self, old, new):
        pass
        # return os.rename(self._full_path(old), self._full_path(new))

    def link(self, target, name):
        pass
        # return os.link(self._full_path(target), self._full_path(name))

    def utimens(self, path, times=None):
        return os.utime(self._at(path), times)

    def open(self, path, flags):
        full_path = self._full_path(path)
        try:
            return os.open(self.items[full_path].name, flags)
        except KeyError:
            raise Exception(errno.ENOENT)

    def create(self, path, mode, fi=None):
        full_path = self._full_path(path)
        if full_path not in self.items:
            self.items[full_path] = TempfileWrapper()
        temp_path = self.items[full_path].name
        return os.open(temp_path, os.O_WRONLY | os.O_CREAT, mode)

    def read(self, path, length, offset, fh):
        full_path = self._full_path(path)
        try:
            return self.items[full_path].read(length, offset)
        except KeyError:
            raise Exception(errno.ENOENT)

    def write(self, path, buf, offset, fh):
        full_path = self._full_path(path)
        try:
            return self.items[full_path].write(buf, offset)
        except KeyError:
            raise Exception(errno.ENOENT)

    def truncate(self, path, length, fh=None):
        full_path = self._full_path(path)
        try:
            return self.items[full_path].truncate(length)
        except KeyError:
            raise Exception(errno.ENOENT)

    def flush(self, path, fh):
        pass

    def release(self, path, fh):
        full_path = self._full_path(path)
        if full_path not in self.items:
            raise Exception(errno.ENOENT)
        # TODO: persist the data

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)
