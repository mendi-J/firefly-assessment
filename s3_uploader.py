#!/usr/bin/env python3
"""
This script uploads analysis reports to an S3 bucket (works with LocalStack).
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("Error: boto3 is required. Install with: pip install boto3", file=sys.stderr)
    sys.exit(1)


class S3Uploader:

    def __init__(self, endpoint_url=None, region="us-east-1"):

        self.region = region

        if endpoint_url:
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                region_name=region,
                aws_access_key_id="test",
                aws_secret_access_key="test",
            )
        else:
            self.s3_client = boto3.client("s3", region_name=region)

    def create_bucket(self, bucket_name):
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            print(f"Bucket '{bucket_name}' already exists.")
        except ClientError:
            try:
                if self.region == "us-east-1":
                    self.s3_client.create_bucket(Bucket=bucket_name)
                else:
                    self.s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={"LocationConstraint": self.region},
                    )
                print(f"Bucket '{bucket_name}' created successfully.")
            except ClientError as e:
                print(f"Error creating bucket: {e}", file=sys.stderr)
                raise

    def upload_report(self, report_data, bucket_name, object_key=None):
        if object_key is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            object_key = f"reports/firefly-report-{timestamp}.json"

        try:
            report_json = json.dumps(report_data, indent=2, ensure_ascii=False)

            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=object_key,
                Body=report_json.encode("utf-8"),
                ContentType="application/json",
                Metadata={
                    "generated-at": datetime.now().isoformat(),
                    "tool": "firefly-analyzer",
                },
            )

            print(f"Report uploaded successfully to s3://{bucket_name}/{object_key}")
            return object_key

        except ClientError as e:
            print(f"Error uploading report: {e}", file=sys.stderr)
            raise

    def upload_file(self, file_path, bucket_name, object_key=None):
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if object_key is None:
            object_key = f"reports/{path.name}"

        try:
            with open(path, "rb") as f:
                self.s3_client.put_object(
                    Bucket=bucket_name,
                    Key=object_key,
                    Body=f.read(),
                    ContentType="application/json",
                )

            print(f"File uploaded successfully to s3://{bucket_name}/{object_key}")
            return object_key

        except ClientError as e:
            print(f"Error uploading file: {e}", file=sys.stderr)
            raise

    def list_reports(self, bucket_name, prefix="reports/"):
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

            if "Contents" not in response:
                return []

            return [obj["Key"] for obj in response["Contents"]]

        except ClientError as e:
            print(f"Error listing reports: {e}", file=sys.stderr)
            raise


def main():
    parser = argparse.ArgumentParser(
        description="Upload Firefly analysis reports to S3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--file", required=True, help="Path to report JSON file")

    parser.add_argument(
        "--bucket",
        default="firefly-reports",
        help="S3 bucket name (default: firefly-reports)",
    )

    parser.add_argument("--key", help="S3 object key (default: auto-generated)")

    parser.add_argument(
        "--endpoint",
        help="Custom S3 endpoint URL (for LocalStack, e.g., http://localhost:4566)",
    )

    parser.add_argument(
        "--region", default="us-east-1", help="AWS region (default: us-east-1)"
    )

    parser.add_argument(
        "--create-bucket",
        action="store_true",
        help="Create bucket if it does not exist",
    )

    parser.add_argument(
        "--list", action="store_true", help="List all reports in the bucket"
    )

    args = parser.parse_args()

    try:
        uploader = S3Uploader(endpoint_url=args.endpoint, region=args.region)

        if args.create_bucket:
            uploader.create_bucket(args.bucket)

        if args.list:
            reports = uploader.list_reports(args.bucket)
            print(f"\nReports in {args.bucket}:")
            for report in reports:
                print(f"  - {report}")
            return 0

        object_key = uploader.upload_file(args.file, args.bucket, args.key)
        print(f"\nSuccess! Access your report at:")

        if args.endpoint:
            print(f"  {args.endpoint}/{args.bucket}/{object_key}")
        else:
            print(
                f"  https://s3.{args.region}.amazonaws.com/{args.bucket}/{object_key}"
            )

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
