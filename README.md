# RetroNASinabox

This is a script to set up a RetroNAS virtual machine (VM) in just a few minutes. 

Normally, it is run as a container on an Unraid server, which will download and set up the VM directly on the server. However, this script can detect whether it is in a container or running just as a script. When running as a script, it should work on any Linux system with kvm/qemu installed, and it will also run in Unraid through the userscripts plugin. The recommended way to run it is on Unraid installed from Community Applications.

## Setting it up

When running on Unraid, the variables are set from the Docker template. When running as a script, the variables are set in the script. Here are the steps to set up the VM:

### Unraid Container

1. Download container from CA
![Download container from CA](https://github.com/SpaceinvaderOne/RetroNASinabox/raw/main/readme%20images/ca_image.png)

2. Set the 'VM Share on Server': &nbsp;&nbsp;&nbsp; to where you store your VMs. The default is /mnt/user/domains.
3. Set the 'RetroNAS data share': &nbsp;&nbsp; to a new share. This is where you will store all your ROMs and other RetroNAS data.
4. Set the 'Name to call VM': &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; to the name you want the VM to have. The default is RetrNAS.
![Template image](https://github.com/SpaceinvaderOne/RetroNASinabox/raw/main/readme%20images/template_image.png)


### Script Install

1. Set the standard_domains_share to the folder where you store your VMs.
2. Set the standard_RETRO_SHARE to a new share. This is where you will store all your ROMs and other RetroNAS data.
3. Set the standard_vm_name to the name you want the VM to have. The default is RetrNAS.

Once the script is run, it will download a vDisk image of Debian 11 with RetroNAS and all its dependencies. The image will be checked against an MD5 checksum to ensure it is the correct image and has not been tampered with. After the image has been downloaded and uncompressed into the qcow2 image, an XML file is created based on the variables set, and then defines (installs) the VM on your server/PC. The RetroNAS data share folder is automatically configured to be connected to the VM by virtiofs. This means if you run your VM on a separate network or VLAN (easy to do on Unraid), RetroNAS can be isolated from your main network.

Once the container or script is run, open the VM in a VNC window. Login with the following credentials:

- Username: retronas
- Password: retronas

At the command prompt, type `retronas`. You will be prompted for your password again. Now you can configure RetroNAS, including setting up usernames, passwords, and other settings.

PS: This installer was made to make the installation process as painless as possible. The real work was done by Dan Mons. His project is available here: https://github.com/danmons/retronas. Thank you, Dan, for making RetroNAS!

