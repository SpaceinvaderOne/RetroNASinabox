"""The guest-side provisioning run, expressed as data.

Keeping this as a string the build hands to cloud-init -- rather than a file
executed somewhere -- means every requirement in the spec can be asserted
without booting anything.
"""

MARKER_OK = "RETRONAS_BUILD_OK"
MARKER_FAIL = "RETRONAS_BUILD_FAILED"

RETRONAS_ROOT_LABEL = "retronas-root"

INSTALLER_URL = "https://raw.githubusercontent.com/retronas/retronas/main/install_retronas.sh"


def provision_script(retronas_ref: str = "main") -> str:
    """Everything the guest does, in order, on its one and only build boot."""
    return f"""#!/bin/bash
set -euo pipefail
trap 'echo {MARKER_FAIL} > /dev/console' ERR

export DEBIAN_FRONTEND=noninteractive

# The account RetroNAS runs as. uid 99 / gid 100 is Unraid's nobody:users, so
# files created on the virtiofs share look normal from the host side. gid 100
# already exists as `users` in the Debian image.
#
# The alias group is not optional: retronas_dependencies.yml chgrps /data to
# `{{{{ retronas_user }}}}` -- the USER variable, not retronas_group -- so a group
# literally named `retronas` must exist or that playbook dies with "failed to
# look up group retronas". `-o` lets it share gid 100, so files still land as
# the gid Unraid calls `users`. Found on hardware, not in review.
groupadd -o -g 100 retronas
useradd --uid 99 --gid 100 --create-home --shell /bin/bash retronas

apt-get update
apt-get install -y --no-install-recommends \\
    qemu-guest-agent unattended-upgrades gdisk git ca-certificates sudo

# Upstream's own installer, fetched the way upstream's own unattended script
# fetches it. Do NOT pre-clone /opt/retronas: install_retronas.sh clones it
# itself, and bails with "Existing installation pass -f to overwrite" and
# exit 1 if the directory is already a checkout. Verified on hardware.
curl -fsSL -o /tmp/install_retronas.sh {INSTALLER_URL}
chmod +x /tmp/install_retronas.sh
/tmp/install_retronas.sh

# Pin the ref only if one other than the installer's default was asked for.
if [ "{retronas_ref}" != "main" ]; then
  git -C /opt/retronas checkout "{retronas_ref}"
fi

cd /opt/retronas/ansible
cp retronas_vars.yml.default retronas_vars.yml
sed -i 's|^retronas_path:.*|retronas_path: /data/retronas|' retronas_vars.yml
sed -i 's|^retronas_group:.*|retronas_group: users|' retronas_vars.yml

ansible-playbook -i hosts.yml retronas_dependencies.yml
ansible-playbook -i hosts.yml install_filesystems.yml
ansible-playbook -i hosts.yml install_cockpit.yml
ansible-playbook -i hosts.yml install_cockpit-retronas.yml

# The label app/retronasdisk.py identifies this image by. Partition 1 is root
# and ships with an empty name, so this is a pure addition.
sgdisk -c 1:{RETRONAS_ROOT_LABEL} /dev/vda

# Every VM built from this image must get its own identity on first boot.
# Sharing a machine-id or an SSH host key across every user's install is not a
# tidiness problem, it is a correctness and impersonation one.
apt-get clean
rm -rf /var/lib/apt/lists/*
rm -f /etc/ssh/ssh_host_*
truncate -s 0 /etc/machine-id
rm -f /var/lib/dbus/machine-id
find /var/log -type f -exec truncate -s 0 {{}} +
cloud-init clean --logs --seed

echo {MARKER_OK} > /dev/console
"""
