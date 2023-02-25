FROM alpine

# Install required dependencies
RUN apk update && apk add bash curl unzip qemu-img sed libvirt gawk util-linux libvirt-client coreutils

# Set the working directory
WORKDIR /app

# Copy the script and xml into the container
COPY letsgo.sh /app/
COPY retro.xml /app/

# Set the file permissions
RUN chmod +x /app/letsgo.sh && \
    chmod 644 /app/retro.xml

# Define the volumes
VOLUME ["/retronas_vm_location", "/retronas_virtiofs_location"]

# Run bash command to keep the container running
CMD ["/bin/bash", "-c", "tail -f /dev/null"]

