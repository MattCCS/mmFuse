#!/usr/bin/env python

"""
This is an attempt at mapping FUSE API calls to REST API calls.
"""

import argparse
import base64
import logging
import urllib.parse
import urllib.request
import pathlib
import psutil

import fuse
import msgpack

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# handler = logging.FileHandler(f"{__name__}.log")
# handler.setLevel(logging.DEBUG)
# logger.addHandler(handler)


def pack_q(args, kwargs, procname):
    bytez = msgpack.packb({"args": args, "kwargs": kwargs, "proc": procname})
    q = base64.urlsafe_b64encode(bytez).decode("utf-8")
    return q


class Fuse2Rest(fuse.Operations):
    FUNC_NAMES = (
        "access", "chmod", "chown", "create",
        "flush", "fsync", "getattr", "link",
        "mkdir", "mknod",

        # File methods
        "open", "read",
        "readdir", "readlink", "release", "rename",
        "rmdir", "statfs", "symlink", "truncate",
        "unlink", "utimens", "write",
    )

    def __init__(self, uri):
        self._uri = uri.rstrip("/")

        for funcname in Fuse2Rest.FUNC_NAMES:
            setattr(self, funcname, self._wrapper(funcname))

    def _api(self, funcname, *args, **kwargs):
        pid = fuse.fuse_get_context()[-1]
        proc = psutil.Process(pid)
        procname = proc.name()

        q = pack_q(args, kwargs, procname)
        url = self._uri + "/" + funcname

        print(f"{url} ({procname})")

        data = urllib.parse.urlencode({"q": q}).encode()
        req = urllib.request.Request(url, data=data)
        result = msgpack.unpackb(urllib.request.urlopen(req).read())
        if result["error"]:
            print(result["error"])
            raise fuse.FuseOSError(result["error"])
        return result["result"]

    def _wrapper(self, funcname):
        def f(*args, **kwargs):
            return self._api(funcname, *args, **kwargs)
        return f


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("mountpoint")
    parser.add_argument("uri")
    return parser.parse_args()


def main():
    args = parse_args()

    volname = pathlib.Path(args.mountpoint).name

    fuse.FUSE(
        Fuse2Rest(args.uri),
        args.mountpoint,
        nothreads=False,
        foreground=True,
        volname=volname,
    )


if __name__ == '__main__':
    main()
