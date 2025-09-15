from __future__ import annotations
import argparse
from importlib.metadata import version, PackageNotFoundError

APP_NAME = "bgm-toolkit-pro"

def get_version() -> str:
    try:
        return version(APP_NAME)
    except PackageNotFoundError:
        return ""

def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="bgm-pro", description="BGM Toolkit Pro CLI")
    p.add_argument("-V", "--version", action="store_true", help="print version")
    args = p.parse_args(argv)

    if args.version:
        print(f"{APP_NAME} {get_version()}".strip())
        return 0

    print("ok")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
