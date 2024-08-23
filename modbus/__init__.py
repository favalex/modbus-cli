#! /usr/bin/env python

import argparse
import sys
import os
import logging
import urllib.parse

import colorama as clr

from modbus_cli.definitions import Definitions
from modbus_cli.modbus_rtu import ModbusRtu
from modbus_cli.modbus_tcp import ModbusTcp
from modbus_cli.access import parse_accesses


class ColourHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.formatter = logging.Formatter("%(style)s%(message)s" + clr.Style.RESET_ALL)

    def emit(self, record):
        if record.levelname == "DEBUG":
            record.style = clr.Style.DIM
        elif record.levelname == "WARNING":
            record.style = clr.Style.BRIGHT
        elif record.levelname == "ERROR":
            record.style = clr.Style.BRIGHT + clr.Fore.RED
        elif record.levelname == "CRITICAL":
            record.style = clr.Style.BRIGHT + clr.Back.BLUE + clr.Fore.RED
        else:
            record.style = clr.Style.NORMAL

        msg = self.format(record)

        print(msg)


def connect_to_device(args):
    if args.device[0] == "/":
        modbus = ModbusRtu(
            device=args.device,
            baud=args.baud,
            parity=args.parity,
            stop_bits=args.stop_bits,
            slave_id=args.slave_id,
            timeout=args.timeout,
        )
    else:
        try:
            result = urllib.parse.urlsplit("//" + args.device)
            host = result.hostname or "localhost"
            port = result.port or 502
        except ValueError:
            logging.error("Invalid device %r", args.device)
            sys.exit(1)

        modbus = ModbusTcp(host, port, args.slave_id, args.timeout)

    modbus.connect()

    return modbus


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--registers", action="append", default=[])
    parser.add_argument("-s", "--slave-id", type=int)
    parser.add_argument("-b", "--baud", type=int, default=19200)
    parser.add_argument("-p", "--stop-bits", type=int, default=1)
    parser.add_argument("-P", "--parity", choices=["e", "o", "n"], default="n")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-S", "--silent", action="store_true")
    parser.add_argument("-t", "--timeout", type=float, default=5.0)
    parser.add_argument(
        "-B", "--byte-order", choices=["le", "be", "mixed"], default="be"
    )
    parser.add_argument("device")
    parser.add_argument("access", nargs="+")
    args = parser.parse_args()

    clr.init()

    try:
        mainLogger = logging.getLogger()  # Main logger

        if args.verbose:
            mainLogger.setLevel(logging.DEBUG)
        else:
            mainLogger.setLevel(logging.INFO)

        ch = ColourHandler()
        mainLogger.addHandler(ch)

        definitions = Definitions(args.silent)
        definitions.parse(
            args.registers + os.environ.get("MODBUS_DEFINITIONS", "").split(":")
        )

        connect_to_device(args).perform_accesses(
            parse_accesses(args.access, definitions, args.byte_order, args.silent),
            definitions,
        ).close()

    finally:
        # restore stdout/stderr if colorama has modified them (mostly on windows)
        # Leaving this out doesn't seem to hurt anything, but they say to call deinit, so we call deinit.
        clr.deinit()


