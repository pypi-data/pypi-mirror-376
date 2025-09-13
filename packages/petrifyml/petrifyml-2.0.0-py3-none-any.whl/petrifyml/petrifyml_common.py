#! /usr/bin/env python3

"""
Common tools for the convertors
"""

def get_args_parser(desc=None):
    import argparse
    import os, sys
    prog_name = os.path.basename(sys.argv[0])
    if desc is None:
        desc = "Convert a ML model to ONNX, or Python or C++ code"
    elif isinstance(desc, list) and len(desc) == 2:
        desc = f"Convert a {desc[0]} to {desc[1]}"
    ap = argparse.ArgumentParser(prog=prog_name, description=desc)
    ap.add_argument("FILE", help="File containing the model")
    ap.add_argument("-n", "--name", dest="NAME", default="decision", help="name to use for the output function and source file [default=%(default)s]")
    ap.add_argument("-v", "--verbose", dest="VERBOSE", action="store_true", help="Print debug output.")
    return ap
