# litesurf/cli.py
import argparse
from .litesurf import main

def cli():
    parser = argparse.ArgumentParser(prog='litesurf', description="litesurf CLI - launches the GUI browser")
    parser.add_argument("--file", "-f", help="Open a local HTML file", default=None)
    parser.add_argument("--url", "-u", help="Open a webpage by URL", default=None)
    args = parser.parse_args()

    # prefer file if both provided
    if args.file:
        main(start_file=args.file)
    else:
        main(start_url=args.url)
