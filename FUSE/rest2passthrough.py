"""
"""

import argparse
import base64
import errno
import json
import logging
import os

from flask import Flask, request
import msgpack

import fuse_clients.passthough
import fuse_clients.buffered_passthrough

FUSE_CLIENT = None

app = Flask(__name__)

(logger := logging.getLogger(__name__)).setLevel(logging.INFO)
logging.getLogger("werkzeug").setLevel(logging.ERROR)


def unpack_q(q):
    bytez = base64.urlsafe_b64decode(q.encode("utf-8"))
    data = msgpack.unpackb(bytez)
    return (data["args"], data["kwargs"], data["proc"])


def call(procname, funcname, *args, **kwargs):
    global FUSE_CLIENT
    FUSE_CLIENT.verify_procname(procname)
    return getattr(FUSE_CLIENT, funcname)(*args, **kwargs)


@app.route('/<funcname>', methods=["POST"])
def callback(funcname):
    global FUSE_CLIENT

    (args, kwargs, procname) = unpack_q(request.form["q"])
    print(f"({procname}) {funcname} {args[:1]}")

    try:
        result = call(procname, funcname, *args, **kwargs)
        out = {"result": result, "error": None}
    except Exception as e:
        # TODO: set explicit value on custom exception object
        print(repr(e))
        out = {"result": None, "error": e.args[0]}

    return msgpack.packb(out)


def parse_args():
    parser = argparse.ArgumentParser()
    # parser.add_argument("client", choices=["passthrough", "mediaman"])
    parser.add_argument("-p", "--passthrough", default=None, help="Path to the passthrough folder")
    parser.add_argument("-m", "--mediman", default=False, action="store_true")
    return parser.parse_args()


def main():
    global FUSE_CLIENT

    args = parse_args()

    if args.passthrough:
        # FUSE_CLIENT = fuse_clients.passthough.Passthrough(args.passthrough)
        FUSE_CLIENT = fuse_clients.buffered_passthrough.BufferedPassthrough(args.passthrough)
    else:
        raise NotImplementedError()

    app.run(threaded=False, port=4001, host="0.0.0.0", debug=True)


if __name__ == '__main__':
    main()
