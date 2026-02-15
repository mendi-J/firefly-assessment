#!/bin/bash
# This script runs the analyzer and uploads the report to S3 (LocalStack)

set -e

echo "=== Firefly Asset Management Pipeline ==="
echo ""

if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

echo "1. Starting LocalStack..."
docker-compose up -d localstack

echo "2. Waiting for LocalStack to be ready..."
sleep 10

echo "3. Checking LocalStack health..."
until docker-compose exec -T localstack awslocal s3 ls > /dev/null 2>&1; do
    echo "   Waiting for S3 service..."
    sleep 3
done
echo "   LocalStack is ready!"

echo ""
echo "4. Running analyzer..."
python3 main.py \
    --cloud examples/cloud_resources.json \
    --iac examples/iac_resources.json \
    --output /tmp/firefly-report.json \
    --pretty

echo ""
echo "5. Uploading report to S3..."
python3 s3_uploader.py \
    --file /tmp/firefly-report.json \
    --bucket firefly-reports \
    --endpoint http://localhost:4566 \
    --create-bucket

echo ""
echo "6. All reports in S3:"
python3 s3_uploader.py \
    --bucket firefly-reports \
    --endpoint http://localhost:4566 \
    --list

echo ""
echo "=== Pipeline Complete ==="
echo ""
echo "To view your report:"
echo "  - Local file: /tmp/firefly-report.json"
echo "  - S3: http://localhost:4566/firefly-reports/reports/..."
echo ""
echo "To stop LocalStack:"
echo "  docker-compose down"
