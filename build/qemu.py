"""Booting a disk under KVM with a bounded deadline, capturing its console."""

from enum import StrEnum
from pathlib import Path

from app.proc import NOT_EXECUTABLE_EXIT_CODE, run

# Debian 13's ovmf package ships the 4M variants; there is no OVMF_CODE.fd.
# Verified on hardware -- the earlier path made QEMU refuse to start at all.
OVMF_CODE = "/usr/share/OVMF/OVMF_CODE_4M.fd"
OVMF_VARS = "/usr/share/OVMF/OVMF_VARS_4M.fd"


class Firmware(StrEnum):
    BIOS = "bios"
    UEFI = "uefi"


class QemuError(Exception):
    """QEMU could not be started."""


def boot_argv(
    disk: str | Path,
    seed: str | Path | None = None,
    *,
    firmware: Firmware = Firmware.BIOS,
    nvram: str | Path | None = None,
    memory_mib: int = 2048,
    vcpus: int = 2,
    network: bool = True,
) -> list[str]:
    argv = [
        "qemu-system-x86_64",
        # Never optional: without KVM this silently drops to TCG emulation and
        # a two-minute build becomes twenty.
        "-enable-kvm",
        "-m",
        str(memory_mib),
        "-smp",
        str(vcpus),
        "-nographic",
        "-drive",
        f"file={disk},if=virtio,format=qcow2",
    ]
    if seed is not None:
        argv += ["-drive", f"file={seed},if=virtio,format=raw,readonly=on"]
    if firmware is Firmware.UEFI:
        # OVMF is a pflash pair, not a -bios blob: read-only firmware plus a
        # writable variable store. `-bios OVMF_CODE...` fails to start QEMU.
        if nvram is None:
            raise QemuError("a UEFI boot needs a writable NVRAM copy; none was given")
        argv += ["-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_CODE}"]
        argv += ["-drive", f"if=pflash,format=raw,file={nvram}"]
    if network:
        argv += ["-netdev", "user,id=n0", "-device", "virtio-net-pci,netdev=n0"]
    else:
        argv += ["-net", "none"]
    return argv


def boot(
    disk: str | Path,
    seed: str | Path | None = None,
    *,
    firmware: Firmware = Firmware.BIOS,
    timeout: float,
    runner=run,
    **kwargs,
) -> str:
    """Boot `disk` and return whatever it printed to the console.

    A boot that hits the deadline still returns its log -- a partial console is
    evidence, and build.milestones decides what it proves. Only a QEMU that
    could not start at all raises, because then there is nothing to judge.
    """
    argv = boot_argv(disk, seed, firmware=firmware, **kwargs)
    code, out, err = runner(argv, timeout=timeout)
    if code == NOT_EXECUTABLE_EXIT_CODE:
        raise QemuError(err.strip() or "qemu-system-x86_64 could not be run")
    return out
