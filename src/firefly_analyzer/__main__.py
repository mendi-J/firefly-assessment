#!/usr/bin/env python3
"""
This script provides a command-line interface for analyzing cloud resources
against IaC resources with optional S3 upload.
"""

import argparse
import json
import sys
from pathlib import Path

from firefly_analyzer import ResourceAnalyzer
from firefly_analyzer.s3_uploader import S3Uploader


def main():
    parser = argparse.ArgumentParser(
        description="Firefly Asset Management - Cloud to IaC Resources Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --cloud cloud.json --iac iac.json
  %(prog)s --cloud cloud.json --iac iac.json --output report.json
  %(prog)s --cloud cloud.json --iac iac.json --pretty
  %(prog)s --cloud cloud.json --iac iac.json --output report.json --upload-s3
  %(prog)s --cloud cloud.json --iac iac.json --upload-s3 --s3-bucket my-bucket
        """,
    )

    parser.add_argument(
        "--cloud", required=True, help="Path to cloud resources JSON file"
    )

    parser.add_argument("--iac", required=True, help="Path to IaC resources JSON file")

    parser.add_argument(
        "--output", "-o", help="Path to output file (default: print to stdout)"
    )

    parser.add_argument(
        "--pretty", "-p", action="store_true", help="Pretty-print JSON output"
    )

    parser.add_argument(
        "--match-keys",
        nargs="+",
        default=["id"],
        help="Keys to use for matching resources (default: id)",
    )

    # S3 upload options
    parser.add_argument(
        "--upload-s3",
        action="store_true",
        help="Upload results to S3 (requires --output)",
    )

    parser.add_argument(
        "--s3-bucket",
        default="firefly-reports",
        help="S3 bucket name (default: firefly-reports)",
    )

    parser.add_argument("--s3-key", help="S3 object key (default: reports/<filename>)")

    parser.add_argument(
        "--s3-endpoint",
        help="Custom S3 endpoint URL (for LocalStack, e.g., http://localhost:4566)",
    )

    parser.add_argument(
        "--s3-region", default="us-east-1", help="AWS region (default: us-east-1)"
    )

    parser.add_argument(
        "--s3-create-bucket",
        action="store_true",
        help="Create S3 bucket if it doesn't exist",
    )

    args = parser.parse_args()

    # Validate S3 upload requirements
    if args.upload_s3 and not args.output:
        parser.error("--upload-s3 requires --output to be specified")

    try:
        analyzer = ResourceAnalyzer(match_keys=args.match_keys)

        print(f"Loading cloud resources from: {args.cloud}", file=sys.stderr)
        print(f"Loading IaC resources from: {args.iac}", file=sys.stderr)

        results = analyzer.analyze_files(args.cloud, args.iac)

        print(
            f"Analysis complete. Processed {len(results)} cloud resource(s).",
            file=sys.stderr,
        )

        # Save or print results
        if args.output:
            analyzer.save_results(results, args.output, pretty=args.pretty)
            print(f"Results saved to: {args.output}", file=sys.stderr)
        else:
            if args.pretty:
                print(json.dumps(results, indent=2, ensure_ascii=False))
            else:
                print(json.dumps(results, ensure_ascii=False))

        # Upload to S3 if requested
        if args.upload_s3:
            print(f"Uploading to S3 bucket: {args.s3_bucket}", file=sys.stderr)

            uploader = S3Uploader(endpoint_url=args.s3_endpoint, region=args.s3_region)

            object_key = uploader.upload_file(
                file_path=args.output,
                bucket_name=args.s3_bucket,
                object_key=args.s3_key,
                create_bucket=args.s3_create_bucket,
            )

            if args.s3_endpoint:
                s3_url = f"{args.s3_endpoint}/{args.s3_bucket}/{object_key}"
            else:
                s3_url = f"https://s3.{args.s3_region}.amazonaws.com/{args.s3_bucket}/{object_key}"

            print(f"Uploaded to: s3://{args.s3_bucket}/{object_key}", file=sys.stderr)
            print(f"URL: {s3_url}", file=sys.stderr)

        # Print summary
        print("\n=== Summary ===", file=sys.stderr)
        missing = sum(1 for r in results if r["State"] == "Missing")
        match = sum(1 for r in results if r["State"] == "Match")
        modified = sum(1 for r in results if r["State"] == "Modified")

        print(f"Missing:  {missing}", file=sys.stderr)
        print(f"Match:    {match}", file=sys.stderr)
        print(f"Modified: {modified}", file=sys.stderr)

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON - {e}", file=sys.stderr)
        return 1

    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
