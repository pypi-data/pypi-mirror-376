import argparse

from . import hello


def main():
    p = argparse.ArgumentParser(description="BGM Toolkit – Labour")
    p.add_argument("--version", action="store_true")
    args = p.parse_args()
    if args.version:
        print("bgm-toolkit-labour 0.1.0")
    else:
        print(hello())
