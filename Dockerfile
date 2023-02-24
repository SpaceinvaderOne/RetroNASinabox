FROM alpine

# Install required dependencies
RUN apk update && apk add curl unzip qemu-img

# Set the working directory
WORKDIR /app

# Copy the script and xml into the container
COPY letsgo.sh .
COPY retro.xml .

# Set the file permissions
RUN chmod +x letsgo.sh && \
    chmod 644 retro.xml

# Define the volumes
VOLUME ["/retronas_vm_location", "/retronas_virtiofs_location"]

# Set the entrypoint
ENTRYPOINT ["/app/letsgo.sh"]
