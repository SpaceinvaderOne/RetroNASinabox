FROM alpine

# Install required dependencies
RUN apk update && apk add bash curl unzip qemu-img

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

# Set the entrypoint
ENTRYPOINT ["/app/letsgo.sh"]

# Sleep for 60 seconds before exiting
CMD ["sh", "-c", "sleep 60"]
