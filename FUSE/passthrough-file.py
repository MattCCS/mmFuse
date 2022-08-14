#!/usr/bin/env python

import argparse
import os
import sys
import tempfile
import errno
import logging
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(f"{__name__}.log")
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

mmlogger = logging.getLogger("mattccs.mediaman")
mmlogger.setLevel(logging.DEBUG)


import fuse
# from refuse import high as fuse

import xattr

import httplib2shim  # NOTE: fixes non-thread-safe httplib2 problems caused by Google's API library
httplib2shim.patch()

import pathlib
# sys.path.append("/Users/matt/home/Repos/Mine/MediaMan/venv/lib/python3.7/site-packages")
# sys.path.append(os.environ.get("MMCONFIG", ""))

from mediaman.core import api  # noqa
import mediaman.core.policy  # noqa
import block_cache  # noqa
import functools  # noqa


SIZES = {}
CACHES = {}


def caller(client, identifier):
    def wrapped(offset, length):
        nonlocal client
        try:
            # return b''.join(api.run_stream_range(
            #     pathlib.Path(),
            #     name,
            #     offset,
            #     length,
            #     service_selector=service
            # ))
            return b''.join(client.stream_range(
                pathlib.Path(),
                identifier,
                offset,
                length,
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
            # hash = self.getxattr(path, "hash")
            results['st_size'] = SIZES[path[1:]]
        except KeyError:
            pass
        return results

    # getxattr = fuse.Operations.getxattr
    setxattr = fuse.Operations.setxattr

    # def getxattr(self, path, name, value, size, *args):
    #     ret = self.operations('getxattr', path.decode(self.encoding),
    #                                       name.decode(self.encoding), *args)

    def getxattr(self, path, name, position=0):
        if position:
            raise fuse.FuseOSError(fuse.ENOTSUP)

        full_path = self._full_path(path)
        return xattr.getxattr(full_path, name).decode('utf-8')

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
        # print(f"read: path={path}, length={length}, offset={offset}")
        # try:
        #     hash = self.getxattr(path, "hash")
        # except OSError:
        #     hash = None
        # print(hash)

        # print(f"fuse.fuse_get_context(): {fuse.fuse_get_context()}")
        pid = fuse.fuse_get_context()[-1]

        import psutil
        proc = psutil.Process(pid)

        logger.info(json.dumps({"proc": (proc.pid, proc.name(), proc.status(), proc.create_time()), "path": path, "offset": offset, "length": length, "size": SIZES[path[1:]]}))
        # logger.info(f"proc={proc} / path={path} / offset={offset} / length={length} / SIZE={SIZES[path[1:]]}")

        if proc.name() in ("AMPLibraryAgent", "QuickLookSatellite"):
            raise fuse.FuseOSError(1)  # "File preview generation disallowed."

        print(f"read: {path, length, offset, fh}")

        # if path.startswith("/xxh64:"):
        #     hash = pathlib.Path(path[1:]).stem
        #     return b''.join(api.run_stream_range(pathlib.Path(), hash, offset, length, service_selector=SERVICE))

        name = path[1:]
        logger.warn(f"filename: {name}")
        # return b''.join(api.run_stream_range(pathlib.Path(), name, offset, length, service_selector=SERVICE))
        if name in CACHES:
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


def prep_mountpoint(root, service, hash=None, fuzzy=None):
    global SIZES, CACHES

    # TODO: blocking to write all files is slow
    if hash:
        results = list(api.run_list(service_selector=service))
        for eresult in results:
            fservice = eresult.client.nickname()
            result = [r for r in eresult.response if hash in r["hashes"]]  # TODO: use URIs instead.
            if result:
                break
        else:
            raise RuntimeError(f"No results in {service} with {hash}")
    elif fuzzy:
        results = list(api.run_fuzzy(fuzzy, service_selector=service))
        for eresult in results:
            fservice = service
            result = list(eresult[1])
            if service == "all":
                result = [f for e in result for f in e.response]
                print(result)
            if result:
                break
        else:
            print(f"No results in " + (service if service else "MediaMan"))
            exit(1)
    else:
        results = list(api.run_list(service_selector=service))
        result = results
        fservice = service
        if service == "all":
            result = [f for e in result for f in e.response]
            print(result)

    (pathlib.Path(root) / ".ql_disablethumbnails").touch()
    # (pathlib.Path(root) / ".ql_disablecache").touch()

    # TODO: cache clients, allow multiple sources
    # TOOD: actually, mm should be caching clients...
    client = mediaman.core.policy.load_client(fservice)
    for f in result:
        hash = f["hashes"][0]

        # filename = f["name"]
        filename = (f["name"] + '-' + hash[6:] + '-' + f["name"])

        SIZES[filename] = f["size"]
        CACHES[filename] = block_cache.BlockwiseBuffer(caller(client, hash), 0)

        filepath = (pathlib.Path(root) / filename)
        filepath.touch()
        # filepath.chmod(0o700)  # RWX
        # xattr.setxattr(filepath, "hash", hash.encode('utf-8'))
        filepath.chmod(0o400)  # read-only

    print(SIZES)
    print(CACHES)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("mountpoint")
    # parser.add_argument("mm_hash")
    parser.add_argument("-f", "--fuzzy")
    parser.add_argument("-s", "--service", default=None, help="MediaMan service name.")
    return parser.parse_args()


def main():
    args = parse_args()

    td = tempfile.TemporaryDirectory()
    prep_mountpoint(td.name, args.service, fuzzy=args.fuzzy)

    fuse.FUSE(Passthrough(td.name), args.mountpoint, nothreads=True, foreground=True)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("[.] User cancelled.")
