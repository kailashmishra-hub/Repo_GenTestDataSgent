# Generative Test Data Agent

This folder contains the CSV index builder for GHCP-assisted test-data lookup.
It also contains a helper for creating new JSON test data from an existing template.

It indexes JSON files from:

```text
users_data/
```

and generates the main input CSV:

```text
.test-data-index/users-index.csv
```

`users-index.csv` captures flattened JSON paths, including nested arrays.

## Build the CSV Index

Run this only when JSON test data changes or when you want to refresh the prepared CSV input:

```powershell
python test_data_agent\build_test_data_index.py
```

GHCP/Copilot should then read:

```text
.test-data-index/users-index.csv
```

Useful columns:

```text
caseInformation.customerID
individual.countryOfResidence
individual.preferredLanguage
individual.postalAddresses[0].countryCode
taxResidencies[0].countryOfTaxResidence
assessments[0].type
assessments[0].resultType
productAgreements[0].productType
productAgreements[0].currency
```

## Create Similar Test Data

Use an existing JSON file as a template and apply explicit overrides:

```powershell
python test_data_agent\create_test_data_from_template.py --template users_data\users2.json --output generated_data\users2_tax_lu.json --set taxResidencies[0].countryOfTaxResidence=LU
```

You can pass multiple `--set` values:

```powershell
python test_data_agent\create_test_data_from_template.py --template users_data\users2.json --output generated_data\new_user.json --set caseInformation.customerID=0099999999 --set individual.preferredLanguage=fr
```

