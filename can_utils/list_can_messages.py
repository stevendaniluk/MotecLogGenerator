#!/usr/bin/env python3

import argparse
import os
import textwrap
import can_utils

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=str, help="Path to logfile")
    parser.add_argument("id", type=str, help="CAN id")

    args = parser.parse_args()

    if args.log:
        args.log = os.path.expanduser(args.log)

    # Make sure our input files are valid
    if not os.path.isfile(args.log):
        print("ERROR: log file %s does not exist" % args.log)
        exit(1)

    with open(args.log, "r") as file:
        lines = file.readlines()

    for line in lines:
        stamp, id, data = can_utils.parse_can_line(line)

        if id == args.id:
            data_bytes = textwrap.wrap(data, 2)
            data_bytes = ' '.join(data_bytes)
            print("%f - %s" % (stamp, data_bytes))
