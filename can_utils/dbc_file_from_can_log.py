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

def get_message_def(id, bytes):
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
    id = id.lstrip("0")

    msg_def = "BO_ " + str(int(id, 16)) + " ID_" + id + ": " + str(bytes) + " TODO\n"
    for i in range(bytes):
        msg_def += "    SG_ ID_" + id + "_B" + str(i + 1) + ": " + str(i * 8) + """|8@1+ (1, 0) [0|254] "" TODO\n"""

    return msg_def

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("log", type=str, help="Path to CAN log")
    parser.add_argument("--output", type=str, help="Path of DBC file to generate, defaults to log")

    args = parser.parse_args()

    if args.log:
        args.log = os.path.expanduser(args.log)

    # Make sure our input files are valid
    if not os.path.isfile(args.log):
        print("ERROR: CAN log '%s' does not exist" % args.log)
        exit(1)

    with open(args.log, "r") as file:
        lines = file.readlines()

    known_ids = can_utils.can_ids_from_lines(lines)

    if not known_ids:
        print("ERROR: No CAN data found in log!")
        exit(1)

    if not args.output:
        args.output = os.path.splitext(args.log)[0] + ".dbc"

    with open(args.output, "w") as file:
        file.write(DBC_HEADER)

        for id, info in sorted(known_ids.items()):
            msg_def = get_message_def(id, info["bytes"])
            file.write("\n")
            file.write(msg_def)

    print("Done!")
