#!/usr/bin/env python

"""
This is an attempt at mapping FUSE API calls to REST API calls.
"""

import argparse
import base64
import logging
import pathlib
import psutil
import socket
import threading
import time
import urllib.parse
import urllib.request

import fuse
import msgpack
import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# handler = logging.FileHandler(f"{__name__}.log")
# handler.setLevel(logging.DEBUG)
# logger.addHandler(handler)


def pack_q(funcname, args, kwargs, procname):
    bytez = msgpack.packb({"funcname": funcname, "args": args, "kwargs": kwargs, "proc": procname})
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
        # self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self._socket.connect(("", int(self._uri.split(":")[-1])))

        self._session = requests.Session()

        for funcname in Fuse2Rest.FUNC_NAMES:
            setattr(self, funcname, self._wrapper(funcname, self._session))

    def _api(self, funcname, session, *args, **kwargs):
        t0 = time.perf_counter()
        thread_id = threading.get_ident()

        pid = fuse.fuse_get_context()[-1]
        print(f"Starting {thread_id=}, {pid=}")
        proc = psutil.Process(pid)
        procname = proc.name()

        q = pack_q(funcname, args, kwargs, procname)

        # SOCKETS = True
        # if SOCKETS:
        #     self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #     self._socket.connect(("", int(self._uri.split(":")[-1])))
        #     # print("sending")
        #     self._socket.send(q + b"\x00\x01\x00\x01\x00\x01\x00\x01")
        #     # print("receiving")
        #     recv = self._socket.recv(10_000_000)  # TODO: 10MB isn't a guarantee
        #     # print("got", recv)
        #     result = msgpack.unpackb(recv)
        #     # print("unpacked")
        #     self._socket.close()

        HTTP = True
        if HTTP:
            url = self._uri + "/" + funcname
            print(f"\t{url} ({procname})")

            # data = urllib.parse.urlencode({"q": q}).encode()
            # req = urllib.request.Request(url, data=data)
            # result = msgpack.unpackb(urllib3.request.urlopen(req).read())
            req = session.post(url, data={"q": q}, stream=True)
            result = msgpack.unpackb(req.raw.read())

        t1 = time.perf_counter()
        dt = t1 - t0
        print(f"\tResolving {thread_id=} after {int(dt*1000)=}ms")

        if result["error"]:
            print(f'\t{result["error"]=}')
            raise fuse.FuseOSError(result["error"])

        return result["result"]

    def _wrapper(self, funcname, session):
        def f(*args, **kwargs):
            return self._api(funcname, session, *args, **kwargs)
        return f


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("mountpoint")
    parser.add_argument("uri")
    return parser.parse_args()


def main():
    args = parse_args()

    volname = pathlib.Path(args.mountpoint).name

    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # Restores CTRL+C functionality

    fuse.FUSE(
        Fuse2Rest(args.uri),
        args.mountpoint,
        nothreads=True,  # True
        foreground=True,  # `False` hangs forever and locks fuse...
        volname=volname,

        # macOS options
        rdonly=True,
        iosize=2**22,  # 2**20
        # blocksize=2**17,  # this corrupts...

        auto_cache=True,
        defer_permissions=True,
        kill_on_unmount=True,
        noappledouble=True,
        noapplexattr=True,
        nobrowse=True,
        nosuid=True,

        noreadahead=False,  # Default.  `True` is extremely slow.

        # # macOS options
        # locallocks=True,
        # nolock=True,
        # rdirplus=True,
        # rsize=1_000_000,  # this crashes entire system...
    )


if __name__ == '__main__':
    main()
