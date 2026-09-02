"""One build, end to end.

Ordering matters and is the spec's: nothing boots until the download is proven
to be Debian's, and nothing is publishable until the finished image has been
booted on its own -- under UEFI, the way Unraid will boot it -- with no seed
driving it.
"""

import shutil
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from app.proc import run
from build import payload, seed, source
from build.milestones import Outcome, booted_ok, read_console, tail
from build.qemu import OVMF_VARS, Firmware
from build.qemu import boot as qemu_boot

PROVISION_TIMEOUT = 45 * 60.0
SMOKE_TIMEOUT = 10 * 60.0
DISK_SIZE = "12G"


class BuildFailed(Exception):
    """The build produced nothing publishable."""


@dataclass(frozen=True, slots=True)
class BuildResult:
    image: Path
    outcome: Outcome
    console: str


def _fetch(url: str, dest: Path) -> Path:
    with urllib.request.urlopen(url, timeout=300) as response, dest.open("wb") as handle:
        while chunk := response.read(1024 * 256):
            handle.write(chunk)
    return dest


def _fetch_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read().decode()


def build(
    workdir,
    *,
    snapshot_id: str = source.SNAPSHOT_ID,
    retronas_ref: str = "main",
    fetch=_fetch,
    sums_fetch=_fetch_text,
    verifier=source.verify,
    runner=run,
    booter=qemu_boot,
    copier=shutil.copyfile,
) -> BuildResult:
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)

    base = workdir / source.image_filename(snapshot_id)
    if not base.exists():
        fetch(source.image_url(snapshot_id), base)
    expected = source.expected_sha512(sums_fetch(source.sums_url(snapshot_id)), base.name)
    verifier(base, expected)

    image = workdir / "retronas.qcow2"
    image.unlink(missing_ok=True)
    code, _out, err = runner(
        [
            "qemu-img",
            "create",
            "-q",
            "-f",
            "qcow2",
            "-b",
            str(base),
            "-F",
            "qcow2",
            str(image),
            DISK_SIZE,
        ]
    )
    if code != 0:
        raise BuildFailed(f"could not create the working image: {err.strip()}")
    if not image.exists():
        # Symmetric with seed.build_iso: an exit code is not proof a file was
        # written, and everything downstream boots this path.
        raise BuildFailed(f"qemu-img reported success but {image} was not written")

    seed_dir = workdir / "seed"
    seed.write_seed(seed_dir, payload.provision_script(retronas_ref), f"build-{snapshot_id}")
    seed_iso = seed.build_iso(seed_dir, workdir / "seed.iso", runner=runner)

    console = booter(image, seed_iso, firmware=Firmware.BIOS, timeout=PROVISION_TIMEOUT)
    # Persist the whole console before judging it. The tail alone is not enough
    # to debug a 45-minute build: cloud-init's poweroff sequence is ~20 lines,
    # so it pushes the failure and its cause out of any short tail.
    console_log = workdir / "provision-console.log"
    console_log.write_text(console)
    outcome = read_console(console)
    if outcome is not Outcome.SUCCEEDED:
        raise BuildFailed(f"provisioning {outcome}; full console at {console_log}\n{tail(console)}")

    # The finished image must come up unaided, under the firmware Unraid uses.
    # OVMF needs its own writable variable store per VM; the system copy is
    # read-only and sharing one between VMs corrupts boot entries.
    nvram = workdir / "OVMF_VARS.fd"
    copier(OVMF_VARS, nvram)
    if not nvram.exists():
        # Symmetric with qemu-img and seed.build_iso above: an exit code (or
        # here, a copier call returning at all) is not proof a file was
        # written, and the smoke boot below depends on this path existing.
        raise BuildFailed(f"the NVRAM copy at {nvram} was not created")
    smoke = booter(image, None, firmware=Firmware.UEFI, nvram=nvram, timeout=SMOKE_TIMEOUT)
    if not booted_ok(smoke):
        raise BuildFailed(f"the finished image did not boot unaided under UEFI:\n{tail(smoke)}")

    return BuildResult(image=image, outcome=Outcome.SUCCEEDED, console=console)
