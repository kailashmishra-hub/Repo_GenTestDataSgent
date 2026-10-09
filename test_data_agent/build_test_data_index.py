import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = [
    PROJECT_ROOT / "users_data",
    PROJECT_ROOT / "generated_data",
]
OUTPUT_DIR = PROJECT_ROOT / ".test-data-index"
INDEX_CSV = OUTPUT_DIR / "users-index.csv"


def flatten_json(item, prefix=""):
    flattened = {}
    if isinstance(item, dict):
        for key, value in item.items():
            child_key = f"{prefix}.{key}" if prefix else key
            flattened.update(flatten_json(value, child_key))
    elif isinstance(item, list):
        if not item:
            flattened[prefix] = ""
        for index, value in enumerate(item):
            child_key = f"{prefix}[{index}]"
            flattened.update(flatten_json(value, child_key))
    else:
        flattened[prefix] = "" if item is None else str(item)
    return flattened


def source_label(json_file, index=None):
    label = json_file.relative_to(PROJECT_ROOT).as_posix()
    return f"{label}#{index}" if index is not None else label


def load_users():
    records = []
    for source_dir in SOURCE_DIRS:
        if not source_dir.exists():
            continue
        for json_file in sorted(source_dir.glob("*.json")):
            with json_file.open(encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, list):
                for index, item in enumerate(data, start=1):
                    records.append({"sourceFile": source_label(json_file, index), **flatten_json(item)})
            else:
                records.append({"sourceFile": source_label(json_file), **flatten_json(data)})
    return records


def fieldnames(records):
    fields = {"sourceFile"}
    for record in records:
        fields.update(record.keys())
    return ["sourceFile"] + sorted(field for field in fields if field != "sourceFile")


def write_csv(records):
    OUTPUT_DIR.mkdir(exist_ok=True)
    with INDEX_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames(records), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def main():
    records = load_users()
    write_csv(records)
    print(f"Indexed {len(records)} user records")
    print(f"Wrote {INDEX_CSV}")


if __name__ == "__main__":
    main()
