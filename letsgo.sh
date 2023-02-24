#!/bin/bash

# Default values for the script. These will be overridden when the script is running in Docker
link1="https://drive.google.com/uc?id=xxxxxxxxxxxxxxxxxxxxx"
link2="https://drive.google.com/uc?id=xxxxxxxxxxxxxxxxxxxxx"
link3="https://drive.google.com/file/d/1g7vxIIH3mxrqmsAfuN3Kib1cbZOfKgex/view?usp=sharing"
vm_name="RetroNAS"
domains_share="/mnt/user/domains"
RETRO_SHARE="/mnt/user/retronas"
XML_FILE="/tmp/retro.xml"

#-----------------------------------------------------------

if [ "$container" = "yes" ]; then
	# Get Variables as they will have been set in Docker as variables and bind mounts
	# link1 get variable from container
	# link2 get variable from container
	# link3 get variable from container
	# vm_name get variable from container
	domains_share=$(find_mappings "/vm_location")
	RETRO_SHARE=$(find_mappings "/virtiofs_location")
	XML_FILE="./retro.xml"
else
	# Use values so can run as a script only with no variable from Docker template
	link1="$link1"
	link2="$link2"
	link3="$link3"
	vm_name="$vm_name"
	domains_share="$domains_share"
	RETRO_SHARE="$RETRO_SHARE"
	expected_checksum="f80ab102b7ab1fec81cfc3d7b929dbd9"
fi

download_location="$domains_share/$vm_name"

#-----------------------------------------------------------

download_retronas() {
    # Expected MD5 checksum for the retronas.zip file
    expected_checksum="f80ab102b7ab1fec81cfc3d7b929dbd9"

    # Create download location if it doesn't exist
    if [ ! -d "$download_location" ]; then
        echo "Download location directory does not exist. Creating it..."
        mkdir -p "$download_location"
    fi

    # Download the file
    for link in "$link1" "$link2" "$link3"; do
        echo "Downloading file from link: $link ..."
        curl -L -c /tmp/cookies "https://drive.google.com/uc?export=download&id=$(echo "$link" | cut -d'/' -f6)" > /dev/null
        confirm=$(awk '/download/ {print $NF}' /tmp/cookies)
        curl -L -b /tmp/cookies "https://drive.google.com/uc?export=download&confirm=$confirm&id=$(echo "$link" | cut -d'/' -f6)" > "$download_location/retronas.zip"

        # Verify the checksum of the downloaded file
        downloaded_checksum=$(md5sum "$download_location/retronas.zip" | cut -d' ' -f1)
        if [ "$downloaded_checksum" != "$expected_checksum" ]; then
            echo "Downloaded file has an incorrect checksum. Trying next link..."
            rm -f "$download_location/retronas.zip"
            continue
        fi

        # Decompress the file
        echo "Decompressing file..."
        unzip -o "$download_location/retronas.zip" -d "$download_location"

        # Check if the file was successfully decompressed
        if [ $? -eq 0 ]; then
            # Delete the original file
            rm -f "$download_location/retronas.zip"

            # Check if vdisk1.img file exists and rename it if it does
            if [ -f "$download_location/vdisk1.img" ]; then
                old_filename=$(date +"vdisk1-old-%Y-%m-%d-%H-%M.img")
                echo "Moving existing vdisk1.img file to $old_filename..."
                mv "$download_location/vdisk1.img" "$download_location/$old_filename"
            fi

            echo "Moving decompressed file to $download_location/vdisk1.img..."
            mv "$download_location/retronas.img" "$download_location/vdisk1.img"
            break
        else
            echo "Failed to decompress file."
            exit 1
        fi
    done
}

#-----------------------------------------------------------

define_retronas() {
	# Generate a random UUID and MAC address
	UUID=$(uuidgen)
	MAC=$(printf '52:54:00:%02X:%02X:%02X\n' $((RANDOM%256)) $((RANDOM%256)) $((RANDOM%256)))

	# Replace the UUID and MAC address tags in the XML file with the generated values
	sed -i "s#<uuid>.*<\/uuid>#<uuid>$UUID<\/uuid>#" "$XML_FILE"
	sed -i "s#<mac address='.*'/>#<mac address='$MAC'/>#" "$XML_FILE"

	# Replace the source file location in the XML file with the download location and filename
	sed -i "s#<source file='.*'/>#<source file='$download_location/vdisk1.img'/>#" "$XML_FILE"

	# Replace the source directory location in the XML file with the specified RetroNAS share directory
	sed -i "s#<source dir='.*'/>#<source dir='$RETRO_SHARE'/>#" "$XML_FILE"

	# Replace the name of the virtual machine in the XML file with the specified name
	sed -i "s#<name>.*<\/name>#<name>$vm_name<\/name>#" "$XML_FILE"
	
	# Replace the icon location in the XML file with the specified location
    sed -i "s#<vmtemplate xmlns=\"unraid\" name=\"RetroNAS\" icon=\"retronas\" os=\"debian\"/>#<vmtemplate xmlns=\"unraid\" name=\"$vm_name\" icon=\"$download_location/RetroNAS_Icon.png\" os=\"debian\"/>#" "$XML_FILE"


	# Define the virtual machine using the modified XML file
	virsh define "$XML_FILE"
}

#-----------------------------------------------------------

function find_mappings {
	# Find the host path of the directory mapped to $1
	HOST_PATH=$(cat /proc/mounts | awk -v dir="$1" '$2 == dir {print $1}')

	echo "$1 is mapped to ${HOST_PATH} on the host"
}

#-----------------------------------------------------------

function download_xml {
	local url="https://raw.githubusercontent.com/SpaceinvaderOne/RetroNASinabox/main/retro.xml"
	curl -s -L $url -o $XML_FILE
}

#-----------------------------------------------------------

function download_icon {
	local url="https://raw.githubusercontent.com/SpaceinvaderOne/RetroNASinabox/main/RetroNAS_Icon.png"
	curl -s -L $url -o $download_location
}

#-----------------------------------------------------------

download_retronas
download_xml
download_icon
define_retronas
echo ""
echo ""
echo ""
echo "Done. Now goto the VMs tab and tou will see the RetroNAS VM installed. Start VM with console VNC "
echo "Start VM with console VNC"
echo "Login with defualt username 'retronas' and passwaord 'retronas'"
echo "Once logged in, type retronas to start the config wizard "

