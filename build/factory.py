"""One build, end to end.

Ordering matters and is the spec's: nothing boots until the download is proven
to be Debian's, and nothing is publishable until the finished image has been
booted on its own -- under UEFI, the way Unraid will boot it -- with no seed
driving it.
"""

import json
import os
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

    # The overlay above is fast to provision on, but it is not what ships: its
    # backing file is a path on the builder's own disk, and a real install
    # target never has that path. Flatten to a plain qcow2 with the same
    # backing data folded in, so the artifact that ships is self-contained.
    flattened = workdir / "retronas.flattened.qcow2"
    flattened.unlink(missing_ok=True)
    code, _out, err = runner(
        ["qemu-img", "convert", "-q", "-O", "qcow2", str(image), str(flattened)]
    )
    if code != 0:
        raise BuildFailed(f"could not flatten the working image: {err.strip()}")
    if not flattened.exists():
        # Symmetric with qemu-img create above: an exit code is not proof a
        # file was written.
        raise BuildFailed(f"qemu-img reported success but {flattened} was not written")
    os.replace(flattened, image)

    # Self-containment is asserted, not assumed: parse qemu-img info's own
    # JSON rather than trust that the convert above did its job.
    code, out, err = runner(["qemu-img", "info", "--output=json", str(image)])
    if code != 0:
        raise BuildFailed(f"could not inspect the flattened image: {err.strip()}")
    try:
        info = json.loads(out)
    except json.JSONDecodeError as exc:
        raise BuildFailed(f"qemu-img info returned unparseable output: {out.strip()!r}") from exc
    if "backing-filename" in info:
        raise BuildFailed(
            f"the flattened image still has a backing file: {info['backing-filename']}"
        )

    # The finished image must come up unaided, under the firmware Unraid
    # uses, with no seed driving it. The Debian base is deleted here, before
    # this boot rather than after, so the boot reproduces the real failure
    # exactly: a real Unraid server never had the base image at all, only
    # the flattened artifact. If the flatten above missed a backing-file
    # reference, this is where that would surface.
    base.unlink()

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
