import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
USERS_DIR = PROJECT_ROOT / "users_data"
INDEX_CSV = PROJECT_ROOT / ".test-data-index" / "users-index.csv"
BUILD_SCRIPT = PROJECT_ROOT / "test_data_agent" / "build_test_data_index.py"


FIELD_ALIASES = {
    "customerID": ["caseInformation.customerID", "customerID"],
    "countryOfResidence": ["individual.countryOfResidence", "countryOfResidence"],
    "preferredLanguage": ["individual.preferredLanguage", "preferredLanguage"],
    "addressCountry": ["individual.postalAddresses[0].countryCode", "addressCountry"],
    "addressCity": ["individual.postalAddresses[0].cityName", "addressCity"],
    "taxCountry": ["taxResidencies[0].countryOfTaxResidence", "taxCountry"],
    "assessmentType": ["assessments[0].type", "assessmentType"],
    "assessmentResult": ["assessments[0].resultType", "assessmentResult"],
    "productType": ["productAgreements[0].productType", "productType"],
    "productCurrency": ["productAgreements[0].currency", "productCurrency"],
    "digitalUsageType": ["individual.digitalAddresses[0].usageType", "digitalUsageType"],
}


def normalize(text):
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def build_index():
    print("Index status     : rebuilding .test-data-index/users-index.csv", flush=True)
    subprocess.run([sys.executable, str(BUILD_SCRIPT)], cwd=PROJECT_ROOT, check=True)


def load_csv_index():
    if not INDEX_CSV.exists():
        raise SystemExit(f"Missing {INDEX_CSV}. Index build did not create users-index.csv.")
    with INDEX_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def add_filter(filters, key, value):
    if value and (key, value) not in filters:
        filters.append((key, value))


def parse_filter(filter_text):
    if "=" not in filter_text:
        raise SystemExit(f"Filter must be key=value, got: {filter_text}")
    key, value = filter_text.split("=", 1)
    return key.strip(), value.strip()


def extract_requirements(request):
    text = request.lower()
    normalized = f" {re.sub(r'[^a-z0-9_=.]+', ' ', text)} "
    filters = []

    for key, value in re.findall(r"([A-Za-z0-9_.\[\]]+)\s*=\s*([A-Za-z0-9_./-]+)", request):
        add_filter(filters, key, value)

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

    address_country = re.search(r"address(?: country)?\s*(?:is|=|as)?\s*([A-Z]{2})\b", request, re.IGNORECASE)
    if address_country:
        add_filter(filters, "addressCountry", address_country.group(1).upper())

    tax_country = re.search(r"tax(?: residency| country)?\s*(?:is|=|as)?\s*([A-Z]{2})\b", request, re.IGNORECASE)
    if tax_country:
        add_filter(filters, "taxCountry", tax_country.group(1).upper())

    if "current account" in normalized or "ordinary account" in normalized:
        add_filter(filters, "productType", "BE_COW_ORDN_AC")
    if "mobile" in normalized:
        add_filter(filters, "digitalUsageType", "MOBILE")

    return filters


def values_for(row, key):
    candidates = FIELD_ALIASES.get(key, [key])
    return [row.get(candidate, "") for candidate in candidates if row.get(candidate, "")]


def first_value(row, key):
    values = values_for(row, key)
    return values[0] if values else ""


def score_row(row, request, filters):
    score = 0
    matched = []
    gaps = []

    for key, expected in filters:
        actual_values = values_for(row, key)
        if any(normalize(actual) == normalize(expected) for actual in actual_values):
            score += 10
            matched.append(f"{key}={expected}")
        else:
            actual = actual_values[0] if actual_values else "<blank>"
            gaps.append(f"{key}: expected {expected}, found {actual}")

    searchable = normalize(" ".join(str(value) for value in row.values()))
    for term in normalize(request).split():
        if len(term) > 1 and term in searchable:
            score += 1

    return score, matched, gaps


def rank_rows(rows, request, filters):
    ranked = []
    for row in rows:
        score, matched, gaps = score_row(row, request, filters)
        ranked.append((score, row, matched, gaps))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked


def decision_for(score, gaps, filter_count):
    if score == 0:
        return "NO_MATCH"
    if filter_count > 0 and not gaps:
        return "EXACT_MATCH"
    if filter_count == 0:
        return "BEST_TEXT_MATCH"
    return "PARTIAL_MATCH"


def source_path(row):
    source = row.get("sourceFile", "")
    return USERS_DIR / source.split("#", 1)[0]


def print_summary(row):
    print(f"Source JSON      : {source_path(row)}")
    print(f"Customer ID      : {first_value(row, 'customerID')}")
    print(f"Residence        : {first_value(row, 'countryOfResidence')}")
    print(f"Language         : {first_value(row, 'preferredLanguage')}")
    print(f"Address country  : {first_value(row, 'addressCountry')}")
    print(f"Tax country      : {first_value(row, 'taxCountry')}")
    print(f"Assessment       : {first_value(row, 'assessmentType')} / {first_value(row, 'assessmentResult')}")
    print(f"Product          : {first_value(row, 'productType')} / {first_value(row, 'productCurrency')}")


def print_json(row):
    path = source_path(row)
    if path.exists():
        print(json.dumps(json.loads(path.read_text(encoding="utf-8")), indent=2))


def main():
    parser = argparse.ArgumentParser(description="Generative test data agent")
    parser.add_argument("request_text", nargs="*", help="Natural-language test data request")
    parser.add_argument("--request", default="", help="Natural-language test data request")
    parser.add_argument("--filter", action="append", default=[], help="Structured key=value requirement")
    parser.add_argument("--top", type=int, default=3, help="Number of candidates to show")
    parser.add_argument("--show-json", action="store_true", help="Print selected JSON content")
    args = parser.parse_args()

    request = args.request or " ".join(args.request_text)

    build_index()

    rows = load_csv_index()
    filters = extract_requirements(request)
    filters.extend(parse_filter(item) for item in args.filter)
    ranked = rank_rows(rows, request, filters)

    if not ranked:
        print("Decision         : NO_DATA")
        return

    best_score, best_row, matched, gaps = ranked[0]
    decision = decision_for(best_score, gaps, len(filters))

    print()
    print("Agent Decision")
    print("=" * 90)
    print(f"Request          : {request or '<no request supplied>'}")
    print(f"Input index      : {INDEX_CSV}")
    print(f"Extracted filters: {', '.join(f'{key}={value}' for key, value in filters) or '<none>'}")
    print(f"Decision         : {decision}")
    print(f"Recommended file : {best_row.get('sourceFile')}")
    if matched:
        print(f"Matched          : {', '.join(matched)}")
    if gaps:
        print("Gaps             :")
        for gap in gaps:
            print(f"  - {gap}")
    print()

    print("Fetched Information")
    print("=" * 90)
    print_summary(best_row)

    if args.show_json:
        print()
        print("Selected JSON")
        print("=" * 90)
        print_json(best_row)

    print()
    print("Candidate Records")
    for score, row, candidate_matched, candidate_gaps in ranked[: args.top]:
        print("=" * 90)
        print(f"Source file      : {row.get('sourceFile')}")
        print(f"Score            : {score}")
        print_summary(row)
        if candidate_matched:
            print(f"Matched          : {', '.join(candidate_matched)}")
        if candidate_gaps:
            print("Gaps             :")
            for gap in candidate_gaps:
                print(f"  - {gap}")


if __name__ == "__main__":
    main()
