#!/usr/bin/env python3

import argparse
import os
import can_utils

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=str, help="Path to logfile")

    args = parser.parse_args()

    if args.log:
        args.log = os.path.expanduser(args.log)

    # Make sure our input files are valid
    if not os.path.isfile(args.log):
        print("ERROR: log file %s does not exist" % args.log)
        exit(1)

    with open(args.log, "r") as file:
        lines = file.readlines()

    known_ids = can_utils.can_ids_from_lines(lines)

    print("ID   | Msg Count")
    print("----------------")
    for id, info in sorted(known_ids.items()):
        print("%s  |  %d" % (id, info["msgs"]))
