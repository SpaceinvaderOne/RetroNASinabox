FROM alpine

# Install required dependencies
RUN apk update && apk add curl unzip qemu-img

# Set the working directory
WORKDIR /app

# Copy the script into the container
COPY letsgo.sh .

# Make the script executable
RUN chmod +x letsgo.sh

# Define the volumes
VOLUME ["/retronas_vm_location", "/retronas_virtiofs_location"]

# Set the entrypoint
ENTRYPOINT ["/app/letsgo.sh"]
