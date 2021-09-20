
import argparse
import hashlib
import json

import matplotlib.pyplot as plt


IGNORED_PROCS = frozenset(["AMPLibraryAgent", "QuickLookSatellite"])

COLORS = {}
LABELS = set()


def plot_logfile(filename):
    with open(filename) as infile:
        events = list(map(json.loads, infile))

    for (i, event) in enumerate(events):
        idx = len(events) - i

        if event["proc"][1] in IGNORED_PROCS:
            continue

        offset = event["offset"]
        length = event["length"]
        size = event["size"]
        path = event["path"]

        if path not in COLORS:
            COLORS[path] = "#" + hashlib.md5(path.encode("utf-8")).hexdigest()[:6]
        hex_color = COLORS[path]

        x0 = offset
        x1 = offset + length

        x0_rel = x0 / size
        x1_rel = x1 / size

        plt.plot([x0_rel, x1_rel], [idx, idx], 'k-', lw=2, color=hex_color, label=None if path in LABELS else path)
        if path not in LABELS:
            LABELS.add(path)

    leg = plt.legend(loc="upper left", ncol=2, mode="expand")
    leg.get_frame().set_alpha(0.5)

    plt.show()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    return parser.parse_args()


def main():
    args = parse_args()
    plot_logfile(args.filename)


if __name__ == '__main__':
    main()
