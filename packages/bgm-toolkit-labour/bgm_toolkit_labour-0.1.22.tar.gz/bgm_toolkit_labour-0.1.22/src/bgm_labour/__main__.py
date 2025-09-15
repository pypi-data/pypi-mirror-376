from __future__ import annotations
import argparse
from importlib.metadata import version, PackageNotFoundError

APP_NAME = "bgm-toolkit-labour"

def get_version() -> str:
    try:
        return version(APP_NAME)
    except PackageNotFoundError:
        return ""

def main() -> int:
    p = argparse.ArgumentParser(prog="bgm-labour", description="BGM Labour toolkit CLI")
    p.add_argument("--version", "-V", action="store_true", help="print version")
    args = p.parse_args()

    if args.version:
        v = get_version()
        print(f"{APP_NAME} {v}".strip())
        return 0

    print("ok")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
