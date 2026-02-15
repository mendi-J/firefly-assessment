# This Dockerfile creates a LocalStack environment with S3 for storing analyzer reports

FROM localstack/localstack:latest

RUN pip install --no-cache-dir boto3

ENV SERVICES=s3
ENV DEFAULT_REGION=us-east-1
ENV DATA_DIR=/tmp/localstack/data
ENV DOCKER_HOST=unix:///var/run/docker.sock

RUN mkdir -p /etc/localstack/init/ready.d

RUN echo '#!/bin/bash\n\
echo "Waiting for LocalStack to be ready..."\n\
awslocal s3 mb s3://firefly-reports\n\
awslocal s3api put-bucket-versioning --bucket firefly-reports --versioning-configuration Status=Enabled\n\
echo "S3 bucket firefly-reports created successfully"\n\
' > /etc/localstack/init/ready.d/setup-s3.sh && \
    chmod +x /etc/localstack/init/ready.d/setup-s3.sh

EXPOSE 4566

HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
  CMD awslocal s3 ls || exit 1

# Start LocalStack
CMD ["docker-entrypoint.sh"]
