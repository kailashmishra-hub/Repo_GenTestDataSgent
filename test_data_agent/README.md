# Generative Test Data Agent

This folder contains the CSV index builder for GHCP-assisted test-data lookup.

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

