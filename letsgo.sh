#!/bin/bash

  #Default values for script. These will be overridden when script running in docker
  link1="https://drive.google.com/uc?id=xxxxxxxxxxxxxxxxxxxxx"
  link2="https://drive.google.com/uc?id=xxxxxxxxxxxxxxxxxxxxx"
  link3="https://drive.google.com/file/d/1g7vxIIH3mxrqmsAfuN3Kib1cbZOfKgex/view?usp=sharing"
  vm_name="RetroNAS"
  domains_share="/mnt/user/domains"
  RETRO_SHARE="/mnt/user/retronas"
  XML_FILE="/other/retro2.xml"
  
  ########################################
  ########################################

if [ "$container" = "yes" ]; then
  # Get Variables as they will have been set in docker as variables and bind mounts
  #link1 get variable from container
  #link2 get variable from container
  #link3 get variable from container
  #vm_name get variable from container
  domains_share=$(find_mappings "/vm_location")
  RETRO_SHARE=$(find_mappings "/virtiofs_location")
  XML_FILE="./retro.xml"
else
  # Use values so can run as script only with no variable from docker template
  link1="link1"
  link2="link2"
  link3="link3"
  vm_name="$vm_name"
  domains_share="$domains_share"
  RETRO_SHARE="$RETRO_SHARE"
  get_xml
fi

 default_download_location="$domains_share/$vm_name"
  
#############################################
download_retronas () {
    

    # Create download location if it doesn't exist
    if [ ! -d "$download_location" ]; then
        echo "Download location directory does not exist. Creating it..."
        mkdir -p "$download_location"
    fi

 

    # Download and decompress the file
    for link in "$link1" "$link2" "$link3"; do
        echo "Downloading file from link: $link ..."
        curl -L -c /tmp/cookies "https://drive.google.com/uc?export=download&id=$(echo "$link" | cut -d'/' -f6)" > /dev/null
        confirm=$(awk '/download/ {print $NF}' /tmp/cookies)
        curl -L -b /tmp/cookies "https://drive.google.com/uc?export=download&confirm=$confirm&id=$(echo "$link" | cut -d'/' -f6)" > "$download_location/retronas.zip"

        # Check if the downloaded file is greater than 500MB
        if [ "$(du -m "$download_location/retronas.zip" | cut -f1)" -ge 500 ]; then
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
        else
            echo "Failed to download file from link: $link"
            rm -f "$download_location/retronas.zip"
        fi
    done
}

###################################################################################

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

  # Define the virtual machine using the modified XML file
  virsh define "$XML_FILE"
}


function find_mappings {
  # Find the host path of the directory mapped to $1
  HOST_PATH=$(cat /proc/mounts | awk -v dir="$1" '$2 == dir {print $1}')

  echo "$1 is mapped to ${HOST_PATH} on the host"
}




download_retronas
define_retronas

echo "done"
