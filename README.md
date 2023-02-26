# RetroNASinabox

This is a script to set up a RetroNAS virtual machine (VM) in just a few minutes. 

Normally, it is run as a container on an Unraid server, which will download and set up the VM directly on the server. However, this script can detect whether it is in a container or running just as a script. When running as a script, it should work on any Linux system with kvm/qemu installed, and it will also run in Unraid through the userscripts plugin. The recommended way to run it is on Unraid installed from Community Applications.

## Setting it up

When running on Unraid, the variables are set from the Docker template. When running as a script, the variables are set in the script. Here are the steps to set up the VM:

### Method 1- Unraid Container

1. Download container from CA

![Download container from CA](https://github.com/SpaceinvaderOne/RetroNASinabox/raw/main/readme%20images/ca_image.png)

2. Set the 'VM Share on Server': &nbsp;&nbsp;&nbsp; to where you store your VMs. The default is /mnt/user/domains.
3. Set the 'RetroNAS data share': &nbsp;&nbsp; to a new share. This is where you will store all your ROMs and other RetroNAS data.
4. Set the 'Name to call VM': &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; to the name you want the VM to have. The default is RetrNAS.

![Template image](https://github.com/SpaceinvaderOne/RetroNASinabox/raw/main/readme%20images/template_image.png)

5. Click apply to pull down and run the container

![Template image](https://github.com/SpaceinvaderOne/RetroNASinabox/raw/main/readme%20images/template_apply.png)

6. Container will run. There is no webui. You can see the progress from clicking on log. Container will run for a couple of minutes. Click on the Unraid VM tab
7. You will see the vm there. Start by clicking Start with console (VNC)

![vm image](https://github.com/SpaceinvaderOne/RetroNASinabox/raw/main/readme%20images/vm_tab.png)

8. Goto Running the VM 


### Method 2- Script Install
The script can be run on a Linux system with kvm/qemu installed.
1. Download script letsgo.sh (or clone this repository)
2. Make script executable
3. Edit below variables to suit
4. Set the standard_domains_share to the folder where you store your VMs.
5. Set the standard_RETRO_SHARE to a new share. This is where you will store all your ROMs and other RetroNAS data.
6. Set the standard_vm_name to the name you want the VM to have. The default is RetrNAS.
7. run script
Once the script is run, it will download a vDisk image of Debian 11 with RetroNAS and all its dependencies. The image will be checked against an MD5 checksum to ensure it is the correct image and has not been tampered with. After the image has been downloaded and uncompressed into the qcow2 image, an XML file is created based on the variables set, and then defines (installs) the VM on your server/PC. The RetroNAS data share folder is automatically configured to be connected to the VM by virtiofs. This means if you run your VM on a separate network or VLAN (easy to do on Unraid), RetroNAS can be isolated from your main network.
8. Run vm

### Running the VM
1. Open a VNC console window to view VM, It will be booting into Debain 11

![debian image](https://github.com/SpaceinvaderOne/RetroNASinabox/raw/main/readme%20images/debian_screen.png)

2. After the above screen you will be greeted with a login screen. Use the below credentials (can be changed later)
- Username: retronas
- Password: retronas

Next start retronas by typing 'retronas' then enter. You will be prompted for your password again

![login image](https://github.com/SpaceinvaderOne/RetroNASinabox/raw/main/readme%20images/login.gif)

3. You will see a user agreement. Click enter then type 'AGREE' to accept
4. The username is set to pi. Change this to retronas
5. The group is set to pi. Change this to retronas. (you can change your password later in the global settings if you want to)

![login image](https://github.com/SpaceinvaderOne/RetroNASinabox/raw/main/readme%20images/config_retronas.gif)
 
 PS: This installer was made to make the installation process as painless as possible. The real work was done by Dan Mons who is the author of RetroNAS. His project is available here: https://github.com/danmons/retronas. Thank you, Dan, for making RetroNAS!

