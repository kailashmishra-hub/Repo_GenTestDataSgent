import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from find_test_data import load_index, parse_filter, print_result, rank_records


PROJECT_ROOT = Path(__file__).resolve().parents[1]
USERS_DIR = PROJECT_ROOT / "users_data"
INDEX_JSON = PROJECT_ROOT / ".test-data-index" / "users-index.json"
BUILD_SCRIPT = PROJECT_ROOT / "test_data_agent" / "build_test_data_index.py"


def run_index_builder():
    subprocess.run([sys.executable, str(BUILD_SCRIPT)], cwd=PROJECT_ROOT, check=True)


def index_is_missing_or_stale():
    if not INDEX_JSON.exists():
        return True

    index_time = INDEX_JSON.stat().st_mtime
    for source_file in USERS_DIR.glob("*.json"):
        if source_file.stat().st_mtime > index_time:
            return True
    return False


def ensure_index(refresh):
    if refresh or index_is_missing_or_stale():
        print("Index status     : refreshing test-data index")
        run_index_builder()
    else:
        print("Index status     : using current test-data index")


def add_filter(filters, key, value):
    if value and (key, value) not in filters:
        filters.append((key, value))


def extract_requirements(request):
    text = request.lower()
    normalized = f" {re.sub(r'[^a-z0-9_=.]+', ' ', text)} "
    filters = []

    for key, value in re.findall(r"([A-Za-z0-9_.\[\]]+)\s*=\s*([A-Za-z0-9_./-]+)", request):
        filters.append(parse_filter(f"{key}={value}"))

    if "belgian" in normalized or "belgium" in normalized or " be " in normalized:
        add_filter(filters, "countryOfResidence", "BE")
    if "french" in normalized or " fr " in normalized:
        add_filter(filters, "preferredLanguage", "fr")
    if "dutch" in normalized or " nl " in normalized:
        add_filter(filters, "preferredLanguage", "nl")

    if "fatca" in normalized:
        add_filter(filters, "assessmentType", "FATCA")
    if "cdd" in normalized:
        add_filter(filters, "assessmentType", "CDD")
    if "crs" in normalized:
        add_filter(filters, "assessmentType", "CRS")

    for result in ["INDSUS", "INDPRV"]:
        if f" {result.lower()} " in normalized:
            add_filter(filters, "assessmentResult", result)

    result_match = re.search(r"(?:assessment\s+)?(?:result|risk)\s*(?:is|=|as)?\s*([LI])\b", request, re.IGNORECASE)
    if result_match:
        add_filter(filters, "assessmentResult", result_match.group(1).upper())

    if "current account" in normalized or "ordinary account" in normalized:
        add_filter(filters, "productType", "BE_COW_ORDN_AC")

    product_match = re.search(r"\b[A-Z]{2}_[A-Z0-9_]+(?:_AC|_CARD|_INS|_DD|_SO)\b", request)
    if product_match:
        add_filter(filters, "productType", product_match.group(0))

    address_country = re.search(r"address(?: country)?\s*(?:is|=|as)?\s*([A-Z]{2})\b", request, re.IGNORECASE)
    if address_country:
        add_filter(filters, "addressCountry", address_country.group(1).upper())

    tax_country = re.search(r"tax(?: residency| country)?\s*(?:is|=|as)?\s*([A-Z]{2})\b", request, re.IGNORECASE)
    if tax_country:
        add_filter(filters, "taxCountry", tax_country.group(1).upper())

    if "mobile" in normalized:
        add_filter(filters, "digitalUsageType", "MOBILE")

    return filters


def decision_for(score, missing, filter_count):
    if score == 0:
        return "NO_MATCH"
    if filter_count > 0 and not missing:
        return "EXACT_MATCH"
    if filter_count == 0:
        return "BEST_TEXT_MATCH"
    return "PARTIAL_MATCH"


def source_path(record):
    source = str(record.get("sourceFile", ""))
    file_name = source.split("#", 1)[0]
    return USERS_DIR / file_name


def print_fetched_information(record, show_json):
    path = source_path(record)
    print("Fetched Information")
    print("=" * 90)
    print(f"Source JSON      : {path}")
    print(f"Customer ID      : {record.get('customerID')}")
    print(f"Language         : {record.get('preferredLanguage')}")
    print(f"Residence        : {record.get('countryOfResidence')}")
    print(f"Address country  : {record.get('addressCountry')}")
    print(f"Tax country      : {record.get('taxCountry')}")
    print(f"Assessment       : {record.get('assessmentType')} / {record.get('assessmentResult')}")
    print(f"Product          : {record.get('productType')} / {record.get('productCurrency')}")

    if show_json and path.exists():
        print()
        print("Selected JSON")
        print("=" * 90)
        print(json.dumps(json.loads(path.read_text(encoding="utf-8")), indent=2))


def main():
    parser = argparse.ArgumentParser(description="Agentic test-data selector")
    parser.add_argument("request_text", nargs="*", help="Natural-language test data request")
    parser.add_argument("--request", default="", help="Natural-language test data request")
    parser.add_argument("--filter", action="append", default=[], help="Structured key=value requirement")
    parser.add_argument("--top", type=int, default=3, help="Number of candidates to show")
    parser.add_argument("--refresh-index", action="store_true", help="Force rebuild before searching")
    parser.add_argument("--show-json", action="store_true", help="Print the selected JSON content")
    args = parser.parse_args()

    request = args.request or " ".join(args.request_text)
    ensure_index(args.refresh_index)

    records = load_index()
    filters = extract_requirements(request)
    filters.extend(parse_filter(item) for item in args.filter)
    ranked = rank_records(records, request, filters)

    if not ranked:
        print("Decision         : NO_DATA")
        print("Reason           : No indexed test data records found.")
        return

    best_score, best_record, best_matched, best_missing = ranked[0]
    decision = decision_for(best_score, best_missing, len(filters))

    print()
    print("Agent Decision")
    print("=" * 90)
    print(f"Request          : {request or '<no request supplied>'}")
    print(f"Extracted filters: {', '.join(f'{key}={value}' for key, value in filters) or '<none>'}")
    print(f"Decision         : {decision}")
    print(f"Recommended file : {best_record.get('sourceFile', '<none>')}")
    print("Reason           : Selected highest-scoring existing test data record.")
    if decision in {"PARTIAL_MATCH", "NO_MATCH"}:
        print("Next action      : Reuse closest file as a template, then change the gap fields.")
    else:
        print("Next action      : Reuse this existing JSON test data file.")
    if best_matched:
        print(f"Matched          : {', '.join(dict.fromkeys(best_matched))}")
    if best_missing:
        print("Gaps             :")
        for item in best_missing:
            print(f"  - {item}")
    print()

    print_fetched_information(best_record, args.show_json)

    print()
    print("Candidate Records")
    for score, record, matched, missing in ranked[: args.top]:
        print_result(record, score, matched, missing)


if __name__ == "__main__":
    main()
