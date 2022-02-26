#!/usr/bin/env python3

def parse_can_line(line):
    stamp, bus, msg = line.split()
    stamp = float(stamp[1:-1])
    id, data = msg.split("#")

    return stamp, id, data

def can_ids_from_lines(lines):
    """Finds all unique CAN ids from logfile and counts the number of messages for each ID.

    return: Dictionary with Id's as keys, and dictionary with maximum byte count and number of
    messages as keys.
    """
    known_ids = {}
    for line in lines:
        stamp, id, data = parse_can_line(line)

        if id in known_ids:
            known_ids[id]["msgs"] += 1
            known_ids[id]["bytes"] = int(max(known_ids[id]["bytes"], len(data) / 2))
        else:
            known_ids[id] = {"msgs": 0, "bytes": 0}

    return known_ids
