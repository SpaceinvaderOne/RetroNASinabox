"""Which Debian image the factory builds on, and proving it is that image.

Two facts here were established by spiking on real hardware, and both look
like needless complication until they bite:

- The variant must be `genericcloud`. Debian's `nocloud` image contains no
  cloud-init whatsoever -- the name means "no cloud", not "the NoCloud
  datasource" -- so it ignores a seed and boots into systemd-firstboot, which
  in CI reads as an unexplained timeout.
- A pinned snapshot directory serves version-suffixed filenames. The bare
  `debian-13-genericcloud-amd64.qcow2` exists only under `latest/`, which is
  exactly what pinning exists to avoid.
"""

import hashlib
from pathlib import Path

SNAPSHOT_ID = "20260819-2575"
VARIANT = "genericcloud"
RELEASE = "trixie"
DEBIAN_MAJOR = "13"
ARCH = "amd64"
BASE_URL = f"https://cloud.debian.org/images/cloud/{RELEASE}"


class ChecksumMissing(Exception):
    """SHA512SUMS carried no line for the file we are about to use."""


class ChecksumMismatch(Exception):
    """The bytes on disk are not the bytes Debian published."""


def image_filename(snapshot_id: str = SNAPSHOT_ID) -> str:
    return f"debian-{DEBIAN_MAJOR}-{VARIANT}-{ARCH}-{snapshot_id}.qcow2"


def image_url(snapshot_id: str = SNAPSHOT_ID) -> str:
    return f"{BASE_URL}/{snapshot_id}/{image_filename(snapshot_id)}"


def sums_url(snapshot_id: str = SNAPSHOT_ID) -> str:
    return f"{BASE_URL}/{snapshot_id}/SHA512SUMS"


def expected_sha512(sums_text: str, filename: str) -> str:
    """The digest SHA512SUMS publishes for exactly `filename`."""
    for line in sums_text.splitlines():
        digest, _, name = line.partition("  ")
        if name.strip() == filename:
            return digest.strip()
    raise ChecksumMissing(f"SHA512SUMS has no entry for {filename}")


def file_sha512(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha512").hexdigest()


def verify(path: Path, expected: str, hasher=file_sha512) -> None:
    """Prove the download is Debian's. A mismatch deletes the file."""
    actual = hasher(path)
    if actual.lower() != expected.lower():
        path.unlink(missing_ok=True)
        raise ChecksumMismatch(
            f"{path.name}: expected {expected.lower()} but got {actual.lower()}; discarded"
        )
