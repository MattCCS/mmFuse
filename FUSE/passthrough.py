#!/usr/bin/env python

import argparse
import os
import sys
import errno

import fuse
# from refuse import high as fuse

import pathlib
# sys.path.append("/Users/matt/home/Repos/Mine/MediaMan/venv/lib/python3.7/site-packages")
# sys.path.append(os.environ.get("MMCONFIG", ""))

from mediaman.core import api  # noqa
import cachetest  # noqa
import cachetest2  # noqa
import functools  # noqa


SIZES = {}
CACHES = {}


def caller(service, name):
    def wrapped(offset, length):
        try:
            return b''.join(api.run_stream_range(
                pathlib.Path(),
                name,
                offset,
                length,
                service_selector=service
            ))
        except RuntimeError as exc:
            raise fuse.FuseOSError(exc)
    return wrapped


class Passthrough(fuse.Operations):
    def __init__(self, root):
        self.root = root

    # Helpers
    # =======

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        # print(f"access: {path, mode}")
        full_path = self._full_path(path)
        if not os.access(full_path, mode):
            raise fuse.FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        # print(f"chmod: {path, mode}")
        full_path = self._full_path(path)
        return os.chmod(full_path, mode)

    def chown(self, path, uid, gid):
        # print(f"chown: {path, uid, gid}")
        full_path = self._full_path(path)
        return os.chown(full_path, uid, gid)

    def getattr(self, path, fh=None):
        # print(f"getattr: {path, fh}")
        full_path = self._full_path(path)
        st = os.lstat(full_path)
        results = dict((key, getattr(st, key)) for key in (
            'st_atime', 'st_ctime', 'st_gid', 'st_mode',
            'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

        # if path.startswith("/xxh64:"):
        #     print(pathlib.Path(path[1:]).stem)
        #     results['st_size'] = SIZES[pathlib.Path(path[1:]).stem]
        #     return results

        try:
            results['st_size'] = SIZES[path[1:]]
        except KeyError:
            pass
        return results

    def readdir(self, path, fh):
        # print(f"readdir: {path, fh}")
        full_path = self._full_path(path)

        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield r

    def readlink(self, path):
        # print(f"readlink: {path}")
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def mknod(self, path, mode, dev):
        # print(f"mknod: {path, mode, dev}")
        return os.mknod(self._full_path(path), mode, dev)

    def rmdir(self, path):
        # print(f"rmdir: {path}")
        full_path = self._full_path(path)
        return os.rmdir(full_path)

    def mkdir(self, path, mode):
        # print(f"mkdir: {path, mode}")
        return os.mkdir(self._full_path(path), mode)

    def statfs(self, path):
        # print(f"statfs: {path}")
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in (
            'f_bavail', 'f_bfree', 'f_blocks', 'f_bsize', 'f_favail',
            'f_ffree', 'f_files', 'f_flag', 'f_frsize', 'f_namemax'))

    def unlink(self, path):
        # print(f"unlink: {path}")
        return os.unlink(self._full_path(path))

    def symlink(self, name, target):
        # print(f"symlink: {name, target}")
        return os.symlink(target, self._full_path(name))

    def rename(self, old, new):
        # print(f"rename: {old, new}")
        return os.rename(self._full_path(old), self._full_path(new))

    def link(self, target, name):
        # print(f"link: {target, name}")
        return os.link(self._full_path(name), self._full_path(target))

    def utimens(self, path, times=None):
        # print(f"utimens: {path, times}")
        return os.utime(self._full_path(path), times)

    # File methods
    # ============

    def open(self, path, flags):
        # print(f"open: {path, flags}")
        full_path = self._full_path(path)
        return os.open(full_path, flags)

    def create(self, path, mode, fi=None):
        # print(f"create: {path, mode, fi}")
        full_path = self._full_path(path)
        return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)

    def read(self, path, length, offset, fh):
        print(f"read: {path, length, offset, fh}")

        # if path.startswith("/xxh64:"):
        #     hash = pathlib.Path(path[1:]).stem
        #     return b''.join(api.run_stream_range(pathlib.Path(), hash, offset, length, service_selector=SERVICE))

        name = path[1:]
        # return b''.join(api.run_stream_range(pathlib.Path(), name, offset, length, service_selector=SERVICE))
        if CACHES:
            return CACHES[name].read(offset, length)

        # import time
        # if time.monotonic() > 10:
        #     return b"f" * length
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)
        # return (b"test " * length)[:length]
        # return (f"{fh} ".encode('utf-8') * length)[:length]

    def write(self, path, buf, offset, fh):
        # print(f"write: {path, buf, offset, fh}")
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def truncate(self, path, length, fh=None):
        # print(f"truncate: {path, length, fh}")
        full_path = self._full_path(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        # print(f"flush: {path, fh}")
        return os.fsync(fh)

    def release(self, path, fh):
        # print(f"release: {path, fh}")
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        # print(f"fsync: {path, fdatasync, fh}")
        return self.flush(path, fh)


def prep_mountpoint(root, service):
    global SIZES, CACHES

    # print(list(api.run_stream_range(pathlib.Path("/Users/matt/Repos/Mine/Experiments/FUSE"), "data.txt", 0, 55)))
    # print(b''.join(api.run_stream_range(pathlib.Path("."), "chipstream.m4a", 65535, 65535, service_selector=service)))
    # print(b''.join(api.run_stream_range(pathlib.Path(), "chipstream.m4a", 0, 4096, service_selector=service)))
    # exit(0)

    filenames = [f for f in os.listdir(root)]
    for f in filenames:
        os.remove(pathlib.Path(root) / f)

    # result = list(api.run_fuzzy(".m4a", service_selector=service))
    # result = list(api.run_fuzzy("chill", service_selector=service))
    # result = list(api.run_fuzzy("wow", service_selector=service))

    # result = list(api.run_search("X3 - Terran Conflict (2008) Full Gameplay-YEU3lKV1HaI.mp4", service_selector=service))
    # result = list(api.run_search("declaration.txt", service_selector=service))
    # result = list(api.run_search("bebopfast.mp4", service_selector=service))
    # result = list(api.run_search("chipstream.m4a", service_selector=service))
    # result = list(api.run_search("12345.txt", service_selector=service))
    # result = list(api.run_search("In Maine.mp4", service_selector=service))

    # result = list(api.run_fuzzy("gits", service_selector=service))
    result = list(api.run_fuzzy("hobbit", service_selector=service))
    result = result[0][1]
    print(result)

    # result = list(api.run_list(service_selector=service))

    (pathlib.Path(root) / ".ql_disablethumbnails").touch()

    for f in result:
        SIZES[f["name"]] = f["size"]
        # CACHES[f["name"]] = cachetest.DumbBytewiseBuffer(caller(service, f["name"]), 10_000_000)
        CACHES[f["name"]] = cachetest2.BlockwiseBuffer(caller(service, f["name"]), 0)
        with open(str(pathlib.Path(root) / f["name"]), "wb") as outfile:
            pass
    print(SIZES)
    print(CACHES)

    # policy = api.policy.load_policy()
    # policy.load_service("drive").authenticate()

    # out = list(api.run_fuzzy("gordon", service_selector="all"))
    # results = list(out[0][1])
    # # results = list(api.run_list(service_selector="all"))
    # # print(results)
    # for result in results:
    #     service_name = result.client.nickname()
    #     for f in result.response:
    #         fname = f["name"]
    #         dname = f'{service_name}>{f["name"]}'
    #         SIZES[dname] = f["size"]
    #         # CACHES[dname] = cachetest.DumbBytewiseBuffer(caller(service, fname), 10_000_000)
    #         CACHES[dname] = cachetest2.BlockwiseBuffer(caller(service_name, fname), 0)
    #         with open(str(pathlib.Path(root) / dname), "wb") as outfile:
    #             pass
    # print(SIZES)
    # print(CACHES)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("mountpoint")
    parser.add_argument("root")
    parser.add_argument("-s", "--service", default=None, help="MediaMan service name.")
    return parser.parse_args()


def main():
    args = parse_args()

    prep_mountpoint(args.root, args.service)

    fuse.FUSE(Passthrough(args.root), args.mountpoint, nothreads=True, foreground=True)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("[.] User cancelled.")
