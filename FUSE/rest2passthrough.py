"""
"""

import argparse
import base64
import logging
import socket

from flask import Flask, request
import msgpack

from FUSE.fuse_clients import passthough
from FUSE.fuse_clients import read_only_passthrough
from FUSE.fuse_clients import tempfile_passthrough


FUSE_CLIENT = None

app = Flask(__name__)

(logger := logging.getLogger(__name__)).setLevel(logging.INFO)
logging.getLogger("werkzeug").setLevel(logging.ERROR)


def unpack_q(q):
    bytez = base64.urlsafe_b64decode(q.encode("utf-8"))
    data = msgpack.unpackb(bytez)
    return (data["funcname"], data["args"], data["kwargs"], data["proc"])


def call(procname, funcname, *args, **kwargs):
    global FUSE_CLIENT
    FUSE_CLIENT.verify_procname(procname)
    return getattr(FUSE_CLIENT, funcname)(*args, **kwargs)


@app.route('/<funcname>', methods=["POST"])
def callback(funcname):
    global FUSE_CLIENT

    (_funcname, args, kwargs, procname) = unpack_q(request.form["q"])
    # print(f"({procname}) {funcname} {args[:1]}")
    if procname == "ls":
        print(f"({procname}) {funcname} {args}")
    elif funcname == "read":
        print(f"({procname}) {funcname} {args}")

    try:
        result = call(procname, funcname, *args, **kwargs)
        out = {"result": result, "error": None}
    except Exception as e:
        # TODO: set explicit value on custom exception object
        print(repr(e))
        # import traceback
        # traceback.print_exc()
        out = {"result": None, "error": e.args[0]}

    return msgpack.packb(out)


def socket_loop():
    _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _socket.bind(("", 4013))
    _socket.listen()
    while True:
        (conn, addr) = _socket.accept()
        with conn:
            # print("Connected by", addr)
            agg = b""
            while True:
                data = conn.recv(10_000_000)  # TODO: 10MB isn't a guarantee
                # print("received")
                if not data:
                    break
                agg += data
                if agg.endswith(b"\x00\x01\x00\x01\x00\x01\x00\x01"):  # TODO: OOF.
                    agg = agg[:-8]
                    break

            # print("unpacking")
            (funcname, args, kwargs, procname) = unpack_q(agg)
            print((procname, funcname, args[:1]))

            try:
                result = call(procname, funcname, *args, **kwargs)
                out = {"result": result, "error": None}
            except Exception as e:
                # TODO: set explicit value on custom exception object
                print(f"{repr(e)} on {funcname} {args[:1]} ({procname})")
                # import traceback
                # traceback.print_exc()
                out = {"result": None, "error": e.args[0]}

            # print("sending")
            conn.sendall(msgpack.packb(out))
            # print("sent")


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
        # FUSE_CLIENT = passthough.Passthrough(args.passthrough)
        FUSE_CLIENT = read_only_passthrough.ReadOnlyPassthrough(args.passthrough)
    else:
        raise NotImplementedError()

    app.run(threaded=True, port=4001, host="0.0.0.0", debug=True)
    # socket_loop()


if __name__ == '__main__':
    main()
