import argparse
import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_JSON = PROJECT_ROOT / ".test-data-index" / "users-index.json"
BUILD_SCRIPT = PROJECT_ROOT / "test_data_agent" / "build_test_data_index.py"


ALIASES = {
    "country": "countryOfResidence",
    "language": "preferredLanguage",
    "assessment": "assessmentType",
    "result": "assessmentResult",
    "product": "productType",
    "address_country": "addressCountry",
    "tax_country": "taxCountry",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "for",
    "i",
    "need",
    "that",
    "the",
    "with",
}

SYNONYMS = {
    "belgian": ["be"],
    "belgium": ["be"],
    "french": ["fr"],
    "dutch": ["nl"],
    "low": ["l"],
    "mobile": ["mobile"],
}


def normalize(text):
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def query_terms(query):
    terms = []
    for term in normalize(query).split():
        if len(term) <= 1 or term in STOPWORDS:
            continue
        terms.append(term)
        terms.extend(SYNONYMS.get(term, []))
    return terms


def load_index():
    if not INDEX_JSON.exists():
        raise SystemExit(
            f"Missing {INDEX_JSON}\nRun first: python {BUILD_SCRIPT.relative_to(PROJECT_ROOT)}"
        )
    return json.loads(INDEX_JSON.read_text(encoding="utf-8"))


def parse_filter(filter_text):
    if "=" not in filter_text:
        raise SystemExit(f"Filter must be key=value, got: {filter_text}")
    key, expected = filter_text.split("=", 1)
    key = ALIASES.get(key.strip(), key.strip())
    return key, expected.strip()


def score_record(record, query_terms, filters):
    score = 0
    matched = []
    missing = []

    for key, expected in filters:
        actual = str(record.get(key, ""))
        if normalize(actual) == normalize(expected):
            score += 10
            matched.append(f"{key}={actual}")
        else:
            missing.append(f"{key}: expected {expected}, found {actual or '<blank>'}")

    searchable = normalize(" ".join(str(value) for value in record.values()))
    for term in query_terms:
        if term in searchable:
            score += 1
            matched.append(term)

    return score, matched, missing


def print_result(record, score, matched, missing):
    print("=" * 90)
    print(f"Source file       : {record.get('sourceFile')}")
    print(f"Customer ID       : {record.get('customerID')}")
    print(f"Country/Language : {record.get('countryOfResidence')} / {record.get('preferredLanguage')}")
    print(f"Address country  : {record.get('addressCountry')}")
    print(f"Tax country      : {record.get('taxCountry')}")
    print(f"Assessment       : {record.get('assessmentType')} / {record.get('assessmentResult')}")
    print(f"Product          : {record.get('productType')} / {record.get('productCurrency')}")
    print(f"Score            : {score}")
    if matched:
        print(f"Matched          : {', '.join(dict.fromkeys(matched))}")
    if missing:
        print("Gaps             :")
        for item in missing:
            print(f"  - {item}")


def main():
    parser = argparse.ArgumentParser(description="Find existing user test data")
    parser.add_argument("--query", default="", help="Natural-language search text")
    parser.add_argument("--filter", action="append", default=[], help="Structured key=value filter")
    parser.add_argument("--top", type=int, default=5, help="Number of results")
    args = parser.parse_args()

    records = load_index()
    filters = [parse_filter(item) for item in args.filter]
    terms = query_terms(args.query)

    ranked = []
    for record in records:
        score, matched, missing = score_record(record, terms, filters)
        ranked.append((score, record, matched, missing))

    ranked.sort(key=lambda item: item[0], reverse=True)
    for score, record, matched, missing in ranked[: args.top]:
        print_result(record, score, matched, missing)


if __name__ == "__main__":
    main()
