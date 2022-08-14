
import abc


class AbstractReadOnlyFuseClient(abc.ABC):
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
        print(f"destroy {path}")
        readonly()

    def chmod(self, path, mode):
        print(f"chmod {path}")
        readonly()

    def chown(self, path, uid, gid):
        print(f"chown {path}")
        readonly()

    def mknod(self, path, mode, dev):
        print(f"mknod {path}")
        readonly()

    def rmdir(self, path):
        print(f"rmdir {path}")
        readonly()

    def mkdir(self, path, mode):
        print(f"mkdir {path}")
        readonly()

    def unlink(self, path):
        print(f"unlink {path}")
        readonly()

    def symlink(self, target, name):
        print(f"symlink {target}")
        readonly()

    def rename(self, old, new):
        print(f"rename {old}")
        readonly()

    def link(self, target, name):
        print(f"link {target}")
        readonly()

    def utimens(self, path, times=None):
        print(f"utimens {path}")
        readonly()

    def create(self, path, mode, fi=None):
        print(f"create {path}")
        readonly()

    def write(self, path, buf, offset, fh):
        print(f"write {path}")
        readonly()

    def truncate(self, path, length, fh=None):
        print(f"truncate {path}")
        readonly()

    def flush(self, path, fh):
        """
        NOTE: OS will call [open > flush > release] even to read a file.
        """
        print(f"flush {path}")
        pass

    def release(self, path, fh):
        """
        NOTE: OS will call [open > flush > release] even to read a file.
        """
        print(f"release {path}")
        pass

    def fsync(self, path, fdatasync, fh):
        print(f"fsync {path}")
        # readonly()
        pass  # iTunes doesn't respect read-only files.
