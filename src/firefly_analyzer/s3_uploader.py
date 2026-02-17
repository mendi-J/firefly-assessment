"""
S3 uploader module for uploading analysis reports to AWS S3 or LocalStack.
"""

import sys
from pathlib import Path
from typing import Optional

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None


class S3Uploader:

    def __init__(self, endpoint_url: Optional[str] = None, region: str = "us-east-1"):

        if boto3 is None:
            raise ImportError(
                "boto3 is required for S3 upload. Install with: pip install boto3"
            )

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

    def upload_file(
        self,
        file_path: str,
        bucket_name: str,
        object_key: Optional[str] = None,
        create_bucket: bool = False,
    ) -> str:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Create bucket if requested
        if create_bucket:
            try:
                self.s3_client.head_bucket(Bucket=bucket_name)
            except ClientError:
                if self.region == "us-east-1":
                    self.s3_client.create_bucket(Bucket=bucket_name)
                else:
                    self.s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={"LocationConstraint": self.region},
                    )

        # Set default object key
        if object_key is None:
            object_key = f"reports/{path.name}"

        # Upload file
        with open(path, "rb") as f:
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=object_key,
                Body=f.read(),
                ContentType="application/json",
            )

        return object_key
