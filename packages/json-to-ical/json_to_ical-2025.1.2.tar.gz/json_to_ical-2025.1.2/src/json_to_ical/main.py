#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
import urllib.request
import urllib.error
from typing import Any


from .convert import create_ical, parse_data, write_calendar_file


def load_json_from_source(source) -> dict[str, Any]:
    try:
        if source.startswith(("http://", "https://")):
            # Get url based data
            print(f"Loading JSON from URL: {source}")
            with urllib.request.urlopen(source) as response:
                return json.loads(response.read().decode())
        else:
            # get file based data
            print(f"Loading JSON from file: {source}")
            with Path(source).open("r") as f:
                return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError, urllib.error.URLError) as e:
        print(f"Error loading JSON data: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """This function probably does too much. It should really just be the CLI interface."""
    parser = argparse.ArgumentParser(description="Convert JSON schedule to iCal format")
    parser.add_argument("source", help="URL or file path to the JSON data")
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output file path for the iCal file (default: pyconau.ics)",
    )
    args = parser.parse_args()
    if not args.output:
        args.output = Path(args.source).stem + ".ics"

    if Path(args.output).exists():
        if (
            input(f"File {args.output} already exists. Overwrite? (y/n): ").lower()
            != "y"
        ):
            print("Exiting...")
            sys.exit(0)

    json_data = load_json_from_source(args.source)
    event_data = parse_data(json_data)
    calendar = create_ical(event_data)

    print(f"Writing {len(calendar.events)} events to {args.output}")
    write_calendar_file(args.output, calendar)

    print(f"Calendar successfully created at {args.output}")


if __name__ == "__main__":
    main()
