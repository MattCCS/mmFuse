
import abc
import errno
import os
import tempfile
import typing


class AbstractBuffer(abc.ABC):

    @abc.abstractmethod
    def read(self, offset, length):
        raise NotImplementedError

    @abc.abstractmethod
    def write(self, data, offset):
        raise NotImplementedError

    @abc.abstractmethod
    def truncate(self, length):
        raise NotImplementedError

    @abc.abstractmethod
    def dump(self):
        raise NotImplementedError


# class MemoryBuffer(AbstractBuffer):

#     def read(self, offset, length):
#         pass

#     def _read(self):
#         pass

#     def _graduate(self):
#         FileBuffer().write(...)


class FileBuffer(AbstractBuffer):
    def __init__(self):
        self.t = tempfile.TemporaryFile()

    def read(self, length, offset):
        self.t.seek(offset)
        return self.t.read(length)

    def write(self, data, offset):
        self.t.seek(offset)
        return self.t.write(data)

    def truncate(self, length):
        return self.t.truncate(length)

    def dump(self):
        # TODO: could use t.write(outbuf) instead
        self.t.seek(0)
        return self.t.read()


def new_buffer():
    return FileBuffer()


class BufferedPassthrough:
    def __init__(self, root):
        self.root = root
        self.buffers: typing.Dict[str, AbstractBuffer] = {}

    def verify_procname(self, procname):
        pass

    def destroy(self, path):
        pass

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    def access(self, path, mode):
        full_path = self._full_path(path)
        if not os.access(full_path, mode):
            # raise FuseOSError(errno.EACCES)
            raise Exception(errno.EACCES)

    def chmod(self, path, mode):
        full_path = self._full_path(path)
        return os.chmod(full_path, mode)

    def chown(self, path, uid, gid):
        full_path = self._full_path(path)
        return os.chown(full_path, uid, gid)

    def getattr(self, path, fh=None):
        full_path = self._full_path(path)
        st = os.lstat(full_path)
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
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def mknod(self, path, mode, dev):
        return os.mknod(self._full_path(path), mode, dev)

    def rmdir(self, path):
        full_path = self._full_path(path)
        return os.rmdir(full_path)

    def mkdir(self, path, mode):
        return os.mkdir(self._full_path(path), mode)

    def statfs(self, path):
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in (
            'f_bavail', 'f_bfree', 'f_blocks', 'f_bsize',
            'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def unlink(self, path):
        return os.unlink(self._full_path(path))

    def symlink(self, target, name):
        return os.symlink(self._full_path(target), self._full_path(name))

    def rename(self, old, new):
        return os.rename(self._full_path(old), self._full_path(new))

    def link(self, target, name):
        return os.link(self._full_path(target), self._full_path(name))

    def utimens(self, path, times=None):
        return os.utime(self._full_path(path), times)

    def open(self, path, flags):
        full_path = self._full_path(path)

        # We make the call, we just don't tell the caller about it
        os.close(os.open(full_path, flags))
        # TODO: respect file flags?

        if full_path not in self.buffers:
            self.buffers[full_path] = new_buffer()
        return 0  # TODO: Does this fake file descriptor work?

    def create(self, path, mode, fi=None):
        full_path = self._full_path(path)

        # We make the call, we just don't tell the caller about it
        os.close(os.open(full_path, os.O_WRONLY | os.O_CREAT, mode))
        # TODO: respect file flags and mode?

        if full_path not in self.buffers:
            self.buffers[full_path] = new_buffer()
        return 0  # TODO: Does this fake file descriptor work?

    def read(self, path, length, offset, fh):
        """
        NOTE: OS will try to read a file created via open().
        """
        # os.lseek(fh, offset, os.SEEK_SET)
        # return os.read(fh, length)
        full_path = self._full_path(path)
        return self.buffers[full_path].read(length, offset)

    def write(self, path, buf, offset, fh):
        # os.lseek(fh, offset, os.SEEK_SET)
        # return os.write(fh, buf)
        full_path = self._full_path(path)
        return self.buffers[full_path].write(buf, offset)

    def truncate(self, path, length, fh=None):
        full_path = self._full_path(path)
        # with open(full_path, 'r+') as f:
        #     f.truncate(length)
        return self.buffers[full_path].truncate(length)

    def flush(self, path, fh):
        # return os.fsync(fh)
        pass  # We don't need to flush to the buffer

    def release(self, path, fh):
        # return os.close(fh)
        full_path = self._full_path(path)
        try:
            buffer = self.buffers[full_path]
        except KeyError:
            return  # Recipient doesn't care what happens on release

        with open(full_path, 'w+b') as outfile:
            outfile.write(buffer.dump())

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)
