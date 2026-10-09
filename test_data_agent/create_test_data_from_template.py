import argparse
import json
import re
from copy import deepcopy
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_path(path):
    parts = []
    for segment in path.split("."):
        match = re.fullmatch(r"([A-Za-z0-9_]+)(?:\[(\d+)])?", segment)
        if not match:
            raise ValueError(f"Unsupported JSON path segment: {segment}")
        parts.append((match.group(1), int(match.group(2)) if match.group(2) is not None else None))
    return parts


def ensure_list_size(items, index):
    while len(items) <= index:
        items.append({})


def set_value(data, path, value):
    current = data
    parts = parse_path(path)
    for position, (key, index) in enumerate(parts):
        is_last = position == len(parts) - 1
        if is_last:
            if index is None:
                current[key] = value
            else:
                current.setdefault(key, [])
                ensure_list_size(current[key], index)
                current[key][index] = value
            return

        next_key, next_index = parts[position + 1]
        if index is None:
            if key not in current or not isinstance(current[key], (dict, list)):
                current[key] = [] if next_index is not None else {}
            current = current[key]
        else:
            current.setdefault(key, [])
            ensure_list_size(current[key], index)
            if not isinstance(current[key][index], dict):
                current[key][index] = {}
            current = current[key][index]

        if isinstance(current, list):
            ensure_list_size(current, next_index or 0)


def parse_setter(setter):
    if "=" not in setter:
        raise ValueError(f"Expected path=value, got: {setter}")
    path, value = setter.split("=", 1)
    return path.strip(), value.strip()


def main():
    parser = argparse.ArgumentParser(description="Create test data by cloning a JSON template and applying overrides")
    parser.add_argument("--template", required=True, help="Existing JSON template file")
    parser.add_argument("--output", required=True, help="Output JSON file to create")
    parser.add_argument("--set", action="append", default=[], help="Override in flattened.path=value format")
    args = parser.parse_args()

    template_path = (PROJECT_ROOT / args.template).resolve() if not Path(args.template).is_absolute() else Path(args.template)
    output_path = (PROJECT_ROOT / args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output)

    with template_path.open(encoding="utf-8") as handle:
        generated = deepcopy(json.load(handle))

    for setter in args.set:
        path, value = parse_setter(setter)
        set_value(generated, path, value)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(generated, indent=2), encoding="utf-8")

    print(f"Template : {template_path}")
    print(f"Output   : {output_path}")
    for setter in args.set:
        print(f"Applied  : {setter}")


if __name__ == "__main__":
    main()
