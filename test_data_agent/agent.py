import argparse
import subprocess
import sys

from find_test_data import load_index, parse_filter, print_result, rank_records


def ensure_index(refresh):
    if not refresh:
        return
    subprocess.run([sys.executable, "test_data_agent/build_test_data_index.py"], check=True)


def decision_for(score, missing, filter_count):
    if score == 0:
        return "NO_MATCH"
    if filter_count > 0 and not missing:
        return "EXACT_MATCH"
    if filter_count == 0:
        return "BEST_TEXT_MATCH"
    return "PARTIAL_MATCH"


def main():
    parser = argparse.ArgumentParser(description="Agentic test-data selector")
    parser.add_argument("--request", default="", help="Natural-language test data request")
    parser.add_argument("--filter", action="append", default=[], help="Structured key=value requirement")
    parser.add_argument("--top", type=int, default=3, help="Number of candidates to show")
    parser.add_argument("--refresh-index", action="store_true", help="Rebuild the index before searching")
    args = parser.parse_args()

    ensure_index(args.refresh_index)
    records = load_index()
    filters = [parse_filter(item) for item in args.filter]
    ranked = rank_records(records, args.request, filters)

    if not ranked:
        print("Decision         : NO_DATA")
        print("Reason           : No indexed test data records found.")
        return

    best_score, best_record, _, best_missing = ranked[0]
    decision = decision_for(best_score, best_missing, len(filters))

    print("Agent Decision")
    print("=" * 90)
    print(f"Decision         : {decision}")
    print(f"Recommended file : {best_record.get('sourceFile', '<none>')}")
    print("Reason           : Selected highest-scoring existing test data record.")
    if decision in {"PARTIAL_MATCH", "NO_MATCH"}:
        print("Next action      : Reuse closest file as a template, then change the gap fields.")
    else:
        print("Next action      : Reuse this existing JSON test data file.")
    print()

    for score, record, matched, missing in ranked[: args.top]:
        print_result(record, score, matched, missing)


if __name__ == "__main__":
    main()
