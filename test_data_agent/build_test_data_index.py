import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
USERS_DIR = PROJECT_ROOT / "users_data"
OUTPUT_DIR = PROJECT_ROOT / ".test-data-index"
INDEX_JSON = OUTPUT_DIR / "users-index.json"
INDEX_CSV = OUTPUT_DIR / "users-index.csv"
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


def load_users():
    records = []
    for json_file in sorted(USERS_DIR.glob("*.json")):
        with json_file.open(encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, list):
            for index, item in enumerate(data, start=1):
                records.append(build_record(f"{json_file.name}#{index}", item))
        else:
            records.append(build_record(json_file.name, data))
    return records


def write_csv(path, records):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(records)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    records = load_users()
    INDEX_JSON.write_text(json.dumps(records, indent=2), encoding="utf-8")
    write_csv(INDEX_CSV, records)
    write_csv(NEO4J_CSV, records)
    print(f"Indexed {len(records)} user records")
    print(f"Wrote {INDEX_JSON}")
    print(f"Wrote {INDEX_CSV}")
    print(f"Wrote {NEO4J_CSV}")


if __name__ == "__main__":
    main()
