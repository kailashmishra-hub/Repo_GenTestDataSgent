import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
USERS_DIR = PROJECT_ROOT / "users_data"
OUTPUT_DIR = PROJECT_ROOT / ".test-data-index"
INDEX_JSON = OUTPUT_DIR / "users-index.json"
INDEX_CSV = OUTPUT_DIR / "users-index.csv"
FULL_INDEX_JSON = OUTPUT_DIR / "users-full-flat.json"
FULL_INDEX_CSV = OUTPUT_DIR / "users-full-flat.csv"
NEO4J_CSV = OUTPUT_DIR / "neo4j-users.csv"


FIELDNAMES = [
    "sourceFile",
    "customerID",
    "involvedPartyType",
    "dataSource",
    "countryOfResidence",
    "preferredLanguage",
    "cityOfBirth",
    "dateOfBirth",
    "gender",
    "maritalStatus",
    "addressCountry",
    "addressCity",
    "digitalUsageType",
    "taxCountry",
    "assessmentType",
    "assessmentResult",
    "productType",
    "productCurrency",
]


def first(items):
    return items[0] if isinstance(items, list) and items else {}


def value(data, *keys):
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return ""
        current = current.get(key)
    return "" if current is None else str(current)


def build_record(source_file, data):
    individual = data.get("individual", {})
    case_info = data.get("caseInformation", {})
    address = first(individual.get("postalAddresses"))
    digital_address = first(individual.get("digitalAddresses"))
    tax_residency = first(data.get("taxResidencies"))
    assessment = first(data.get("assessments"))
    product = first(data.get("productAgreements"))

    return {
        "sourceFile": source_file,
        "customerID": value(case_info, "customerID"),
        "involvedPartyType": value(case_info, "involvedPartyType"),
        "dataSource": value(individual, "dataSource"),
        "countryOfResidence": value(individual, "countryOfResidence"),
        "preferredLanguage": value(individual, "preferredLanguage"),
        "cityOfBirth": value(individual, "cityOfBirth"),
        "dateOfBirth": value(individual, "dateOfBirth"),
        "gender": value(individual, "gender"),
        "maritalStatus": value(individual, "maritalStatus"),
        "addressCountry": value(address, "countryCode"),
        "addressCity": value(address, "cityName"),
        "digitalUsageType": value(digital_address, "usageType"),
        "taxCountry": value(tax_residency, "countryOfTaxResidence"),
        "assessmentType": value(assessment, "type"),
        "assessmentResult": value(assessment, "resultType"),
        "productType": value(product, "productType"),
        "productCurrency": value(product, "currency"),
    }


def flatten_json(item, prefix=""):
    flattened = {}
    if isinstance(item, dict):
        for key, value_to_flatten in item.items():
            child_key = f"{prefix}.{key}" if prefix else key
            flattened.update(flatten_json(value_to_flatten, child_key))
    elif isinstance(item, list):
        if not item:
            flattened[prefix] = ""
        for index, value_to_flatten in enumerate(item):
            child_key = f"{prefix}[{index}]"
            flattened.update(flatten_json(value_to_flatten, child_key))
    else:
        flattened[prefix] = "" if item is None else str(item)
    return flattened


def load_users():
    records = []
    flat_records = []
    for json_file in sorted(USERS_DIR.glob("*.json")):
        with json_file.open(encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, list):
            for index, item in enumerate(data, start=1):
                source_file = f"{json_file.name}#{index}"
                records.append(build_record(source_file, item))
                flat_records.append({"sourceFile": source_file, **flatten_json(item)})
        else:
            records.append(build_record(json_file.name, data))
            flat_records.append({"sourceFile": json_file.name, **flatten_json(data)})
    return records, flat_records


def write_csv(path, records, fieldnames):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def full_fieldnames(records):
    fields = {"sourceFile"}
    for record in records:
        fields.update(record.keys())
    return ["sourceFile"] + sorted(field for field in fields if field != "sourceFile")


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    records, flat_records = load_users()
    INDEX_JSON.write_text(json.dumps(records, indent=2), encoding="utf-8")
    FULL_INDEX_JSON.write_text(json.dumps(flat_records, indent=2), encoding="utf-8")
    write_csv(INDEX_CSV, records, FIELDNAMES)
    write_csv(FULL_INDEX_CSV, flat_records, full_fieldnames(flat_records))
    write_csv(NEO4J_CSV, records, FIELDNAMES)
    print(f"Indexed {len(records)} user records")
    print(f"Wrote {INDEX_JSON}")
    print(f"Wrote {INDEX_CSV}")
    print(f"Wrote {FULL_INDEX_JSON}")
    print(f"Wrote {FULL_INDEX_CSV}")
    print(f"Wrote {NEO4J_CSV}")


if __name__ == "__main__":
    main()
