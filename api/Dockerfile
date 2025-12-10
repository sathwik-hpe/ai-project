FROM python:3.12-slim

WORKDIR /app

# Install kubectl and ca-certificates
RUN apt-get update && \
    apt-get install -y ca-certificates curl && \
    update-ca-certificates && \
    curl -k -LO "https://dl.k8s.io/release/v1.31.0/bin/linux/arm64/kubectl" && \
    chmod +x kubectl && \
    mv kubectl /usr/local/bin/ && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Update Python SSL certificates and link to system certs
RUN python -m pip install --upgrade certifi && \
    ln -sf /etc/ssl/certs/ca-certificates.crt $(python -m certifi)

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY agent_service.py .

# Expose port
EXPOSE 8000

# Set SSL certificate environment variables
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

# Create entrypoint script to fix kubeconfig
RUN echo '#!/bin/bash\n\
if [ -f /root/.kube/config ]; then\n\
  cp /root/.kube/config /tmp/kubeconfig\n\
  sed -i "s/127.0.0.1/host.docker.internal/g" /tmp/kubeconfig\n\
  sed -i "s/certificate-authority-data:.*/insecure-skip-tls-verify: true/g" /tmp/kubeconfig\n\
  export KUBECONFIG=/tmp/kubeconfig\n\
fi\n\
exec python agent_service.py' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Run the service
CMD ["/app/entrypoint.sh"]
