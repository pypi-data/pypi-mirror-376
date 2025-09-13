# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Copyright (c) 2021
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

# --------------------
# System wide imports
#  -------------------

import sys
import logging
from logging import StreamHandler
from logging.handlers import WatchedFileHandler
import traceback
from argparse import ArgumentParser, Namespace
from typing import Callable

# -------------
# Local imports
# -------------


# -----------------------
# Module global variables
# -----------------------

# get the root logger
log = logging.getLogger()

# ------------------------
# Module utility functions
# ------------------------


def configure_logging(args: Namespace):
    """Configure the root logger"""
    global log
    if args.verbose:
        level = logging.DEBUG
    elif args.quiet:
        level = logging.WARNING
    else:
        level = logging.INFO
    # set the root logger level
    log.setLevel(level)
    # Log formatter
    # fmt = logging.Formatter('%(asctime)s - %(name)s [%(levelname)s] %(message)s')
    fmt = logging.Formatter("%(asctime)s [%(levelname)-8s] [%(name)s] %(message)s")
    # create console handler and set level to debug
    if args.console:
        ch = StreamHandler()
        ch.setFormatter(fmt)
        ch.setLevel(logging.DEBUG)
        log.addHandler(ch)
    # Create a file handler suitable for logrotate usage
    if args.log_file:
        fh = WatchedFileHandler(args.log_file)
        # fh = logging.handlers.TimedRotatingFileHandler(args.log_file, when='midnight', interval=1, backupCount=365)
        fh.setFormatter(fmt)
        fh.setLevel(logging.DEBUG)
        log.addHandler(fh)


def arg_parser(name: str, version: str, description: str) -> ArgumentParser:
    # create the top-level parser
    parser = ArgumentParser(prog=name, description=description)
    # Generic args common to every command
    parser.add_argument(
        "--version", action="version", version="{0} {1}".format(name, version)
    )
    parser.add_argument("--console", action="store_true", help="Log to console.")
    parser.add_argument(
        "--log-file", type=str, metavar="<FILE>", default=None, help="Log to file."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--verbose", action="store_true", help="Verbose output.")
    group.add_argument("--quiet", action="store_true", help="Quiet output.")
    parser.add_argument("--trace", action="store_true", help="Show exception stack trace.")
    return parser


def execute(
    main_func: Callable[[Namespace], None],
    add_args_func: Callable[[ArgumentParser], None],
    name: str,
    version: str,
    description: str,
) -> None:
    try:
        return_code = 1
        parser = arg_parser(name, version, description)
        add_args_func(parser)  # Adds more arguments
        args = parser.parse_args(sys.argv[1:])
        configure_logging(args)
        log.info(f"============== {name} {version} ==============")
        main_func(args)
        return_code = 0
    except KeyboardInterrupt:
        log.critical("[%s] Interrupted by user ", name)
    except Exception as e:
        log.critical("[%s] Fatal error => %s", name, str(e))
        if args.trace:
            traceback.print_exc()
    finally:
        sys.exit(return_code)
