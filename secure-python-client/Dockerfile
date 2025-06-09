FROM registry.access.redhat.com/ubi9/ubi-minimal:latest

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN microdnf update -y && \
    microdnf install -y python3 python3-pip && \
    microdnf clean all
RUN pip install --no-cache-dir -r requirements.txt

# Set the working directory
WORKDIR /opt/app

# Copy application files
COPY secure_client.py .
COPY secure_producer.py .
COPY secure_consumer.py .
COPY secure_common.py .

# Create a directory for config files
RUN mkdir -p /opt/app/config

# Set default entrypoint to use the unified client
ENTRYPOINT ["python3", "secure_client.py"]

# Default command (can be overridden)
CMD ["--help"]