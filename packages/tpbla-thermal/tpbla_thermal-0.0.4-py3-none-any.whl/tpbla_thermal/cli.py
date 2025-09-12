import argparse
from . import __version__
from .gui import main as _gui_main

def main():
    parser = argparse.ArgumentParser(prog="tpbla-thermal", description="TPBLA_ThermAL CLI")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    args = parser.parse_args()

    if args.version:
        print(f"tpbla-thermal {__version__}")
        return

    # Default: launch GUI
    _gui_main()

