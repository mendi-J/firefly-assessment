#!/usr/bin/env python3
"""
This script provides a command-line interface for analyzing cloud resources
against IaC resources.
"""

import argparse
import json
import sys
from pathlib import Path

from analyzer import ResourceAnalyzer


def main():

    parser = argparse.ArgumentParser(
        description="Firefly Asset Management - Cloud to IaC Resources Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --cloud cloud.json --iac iac.json
  %(prog)s --cloud cloud.json --iac iac.json --output report.json
  %(prog)s --cloud cloud.json --iac iac.json --pretty
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

    args = parser.parse_args()

    try:
        analyzer = ResourceAnalyzer(match_keys=args.match_keys)

        print(f"Loading cloud resources from: {args.cloud}", file=sys.stderr)
        print(f"Loading IaC resources from: {args.iac}", file=sys.stderr)

        results = analyzer.analyze_files(args.cloud, args.iac)

        print(
            f"Analysis complete. Processed {len(results)} cloud resource(s).",
            file=sys.stderr,
        )

        if args.output:
            analyzer.save_results(results, args.output, pretty=args.pretty)
            print(f"Results saved to: {args.output}", file=sys.stderr)
        else:
            if args.pretty:
                print(json.dumps(results, indent=2, ensure_ascii=False))
            else:
                print(json.dumps(results, ensure_ascii=False))

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

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
