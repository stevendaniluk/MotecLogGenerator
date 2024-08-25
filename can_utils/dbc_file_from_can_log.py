#!/usr/bin/env python3

import argparse
import os
import can_utils

DESCRIPTION = """Generates a DBC file with individual signals for every byte from every CAN id
present in a log file."""

DBC_HEADER = """VERSION "TODO"

NS_ :
    BA_
    BA_DEF_
    BA_DEF_DEF_
    BA_DEF_DEF_REL_
    BA_DEF_REL_
    BA_DEF_SGTYPE_
    BA_REL_
    BA_SGTYPE_
    BO_TX_BU_
    BU_BO_REL_
    BU_EV_REL_
    BU_SG_REL_
    CAT_
    CAT_DEF_
    CM_
    ENVVAR_DATA_
    EV_DATA_
    FILTER
    NS_DESC_
    SGTYPE_
    SGTYPE_VAL_
    SG_MUL_VAL_
    SIGTYPE_VALTYPE_
    SIG_GROUP_
    SIG_TYPE_REF_
    SIG_VALTYPE_
    VAL_
    VAL_TABLE_

BS_:

BU_: TODO
"""

def get_dbc_message_def(id, bytes):
    """ Generates a DBC file message definition for a particular CAN id with one signal for each
    byte present.

    Example, for the CAN id 0x002 which has 3 bytes of data the following would be produced:
        BO_ 2 002: 8 TODO
            SG_ 002_B1: 0|8@1+ (1, 0) [0|254] "" TODO
            SG_ 002_B2: 8|8@1+ (1, 0) [0|254] "" TODO
            SG_ 002_B3: 16|8@1+ (1, 0) [0|254] "" TODO

    :id: CAN id in hex
    :bytes: Number of bytes of data from this id
    """
    id_hex = id.lstrip("0")
    id_field = int(id_hex, 16)
    if id_field > 2047:
        # This is an extended frame. The DBC file spec does not provide a flag
        # to indicate this, instead a single bit in the id field is used instead
        # so we have to set that manually.
        id_field += 0x80000000

    msg_def = "BO_ " + str(id_field) + " ID_" + id_hex + ": " + str(max(bytes) + 1) + " TODO\n"
    for i in bytes:
        msg_def += "    SG_ ID_" + id_hex + "_B" + str(i + 1) + ": " + str(i * 8) + """|8@1+ (1, 0) [0|254] "" TODO\n"""

    return msg_def

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("log", type=str, help="Path to CAN log")
    parser.add_argument("--output", type=str, help="Path of DBC file to generate, defaults to log")
    parser.add_argument("--use_min_bytes", action="store_true", \
        help="Use the minimum number of bytes observed for the DBC file")
    parser.add_argument("--ignore_constant", action="store_true", \
        help="Ignore any channels that have constant data across the entire log")
    parser.add_argument("--min_frequency", type=float, default=None, \
        help="Minimum frequency, below which an ID is ignore")
    parser.add_argument("--max_frequency", type=float, default=None, \
        help="Maximum frequency, below which an ID is ignore")

    args = parser.parse_args()

    if args.log:
        args.log = os.path.expanduser(args.log)

    # Make sure our input files are valid
    if not os.path.isfile(args.log):
        print("ERROR: CAN log '%s' does not exist" % args.log)
        exit(1)

    if not args.output:
        args.output = os.path.splitext(args.log)[0] + ".dbc"

    with open(args.log, "r") as file:
        lines = file.readlines()

    id_stats = can_utils.get_id_stats_from_lines(lines)

    if not id_stats:
        print("ERROR: No CAN data found in log!")
        exit(1)

    with open(args.output, "w") as file:
        file.write(DBC_HEADER)

        for id, stats in sorted(id_stats.items()):
            # Prune based on frequency
            avg_hz = stats.avg_frequency()
            if args.min_frequency and avg_hz < args.min_frequency:
                continue
            if args.max_frequency and avg_hz > args.max_frequency:
                continue

            # Filter which bytes to select
            max_byte_num = stats.bytes_min if args.use_min_bytes else stats.bytes_max
            if args.ignore_constant:
                bytes = []
                for i in range(max_byte_num):
                    if stats.byte_stats[i].range > 0:
                        bytes.append(i)
            else:
                bytes = list(range(max_byte_num))

            if not bytes:
                continue

            msg_def = get_dbc_message_def(id, bytes)
            file.write("\n")
            file.write(msg_def)

    print("Done!")
