"""Build a RetroNAS appliance image."""

import argparse
import sys

from build.factory import BuildFailed, build
from build.qemu import QemuError
from build.seed import SeedError
from build.source import SNAPSHOT_ID, ChecksumMismatch, ChecksumMissing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="build")
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--snapshot", default=SNAPSHOT_ID)
    parser.add_argument("--retronas-ref", default="main")
    args = parser.parse_args(argv)

    try:
        result = build(
            args.workdir,
            snapshot_id=args.snapshot,
            retronas_ref=args.retronas_ref,
        )
    except (
        BuildFailed,
        ChecksumMismatch,
        ChecksumMissing,
        SeedError,
        QemuError,
        OSError,
    ) as err:
        print(f"Build failed: {err}")
        return 1

    print(f"Built and smoke-tested: {result.image}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
