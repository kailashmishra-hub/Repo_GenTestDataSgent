import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "runtime" / "data-finder--report.txt"


def read_content(args):
    if args.text:
        return args.text
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return "No report content was provided."


def main():
    parser = argparse.ArgumentParser(description="Write the data finder report to runtime/data-finder--report.txt")
    parser.add_argument("--text", help="Report content to write")
    args = parser.parse_args()

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(read_content(args).rstrip() + "\n", encoding="utf-8")

    if not REPORT_PATH.exists():
        raise SystemExit(f"Report was not created: {REPORT_PATH}")

    print(f"Report written: {REPORT_PATH}")


if __name__ == "__main__":
    main()
