"""The cloud-init NoCloud seed the build hands to the guest."""

from pathlib import Path

from app.proc import run

ISO_TIMEOUT = 60.0

# cloud-init's NoCloud datasource looks for a filesystem with this exact volume
# label. Get it wrong and the seed is ignored without complaint.
VOLUME_LABEL = "cidata"


class SeedError(Exception):
    """The seed ISO could not be built."""


def user_data(script: str) -> str:
    indented = "\n".join("      " + line for line in script.splitlines())
    # The explicit "2" on "|2" pins the block scalar's indentation at 2 spaces
    # beyond the parent node (content: at 4 -> block starts at 6) rather than
    # letting YAML infer it from the first non-empty line. Without it, a
    # script whose first line happens to be indented MORE than a later line
    # (e.g. a script starting inside an `if` block) makes YAML detect too
    # deep an indent, so the shallower later line falls outside the block and
    # breaks the document. That failure is invisible here -- user_data()
    # still returns a string -- and invisible in the guest too: cloud-init
    # just silently ignores an unparsable seed and boots unconfigured.
    return f"""#cloud-config
write_files:
  - path: /var/lib/retronas-build/provision.sh
    permissions: '0755'
    content: |2
{indented}
runcmd:
  - [ /var/lib/retronas-build/provision.sh ]
power_state:
  mode: poweroff
  timeout: 30
  condition: true
"""


def meta_data(instance_id: str) -> str:
    return f"instance-id: {instance_id}\nlocal-hostname: retronas-build\n"


def write_seed(directory: Path, script: str, instance_id: str) -> tuple[Path, Path]:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    user = directory / "user-data"
    meta = directory / "meta-data"
    user.write_text(user_data(script))
    meta.write_text(meta_data(instance_id))
    return user, meta


def build_iso(seed_dir: Path, output: Path, runner=run) -> Path:
    seed_dir, output = Path(seed_dir), Path(output)
    code, _out, err = runner(
        [
            "xorriso",
            "-as",
            "mkisofs",
            "-quiet",
            "-output",
            str(output),
            "-volid",
            VOLUME_LABEL,
            "-joliet",
            "-rock",
            str(seed_dir / "user-data"),
            str(seed_dir / "meta-data"),
        ],
        timeout=ISO_TIMEOUT,
    )
    if code != 0:
        raise SeedError(f"xorriso failed ({code}): {err.strip() or 'no output'}")
    if not output.exists():
        raise SeedError(f"xorriso reported success but {output} was not written")
    return output
