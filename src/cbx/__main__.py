#!/bin/python3

import argparse
from pathlib import Path
from . import convert

import logging


def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="file to convert")
    parser.add_argument("--dpi", type=int, help="PDF DPI", default=300)
    args = parser.parse_args()
    convert(Path(args.input), args.dpi)


if __name__ == "__main__":
    main()
