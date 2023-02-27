FROM alpine:latest

# Install required dependencies needed for the container
RUN apk update && apk upgrade && \
    apk add bash curl unzip qemu-img sed libvirt gawk util-linux libvirt-client coreutils && \
    apk add --no-cache python3 && \
    pip3 install gdown

# Set  working directory here
WORKDIR /app

# Copy the assets into the container
COPY letsgo.sh /app/
COPY retro.xml /app/

# Set permissions
RUN chmod +x /app/letsgo.sh && \
    chmod 644 /app/retro.xml

# Set  entrypoint
ENTRYPOINT ["/app/letsgo.sh"]

# Sleep for 60 seconds before exiting
CMD ["sh", "-c", "sleep 60"]
