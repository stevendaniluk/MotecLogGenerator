#!/usr/bin/env python3

import argparse
import os

DESCRIPTION = """Convertes a candump recorded with options '-ta' for human
 readable format to one recorded with '-l' which can be replayed with canplayer"""

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("log", type=str, help="Path to logfile")
    parser.add_argument("--output", type=str, help="New file to write to, defaults to 'log'.converted")

    args = parser.parse_args()

    if args.log:
        args.log = os.path.expanduser(args.log)

    # Make sure our input file is valid
    if not os.path.isfile(args.log):
        print("ERROR: log file %s does not exist" % args.log)
        exit(1)

    if not args.output:
        args.output = args.log + ".converted"

    with open(args.log, "r") as file:
        lines = file.readlines()

    with open(args.output, "w") as file:
        for line in lines:
            line_split = line.split()
            stamp = line_split[0]
            bus = line_split[1]
            id = line_split[2]
            msg = "".join(line_split[4:])

            new_line = "{} {} {}#{}\n".format(stamp, bus, id, msg)
            file.write(new_line)
