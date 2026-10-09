# Generative Test Data Agent

This folder contains the local test-data agent for GHCP-assisted testing.

It indexes JSON files from:

```text
users_data/
```

and generates the main input CSV:

```text
.test-data-index/users-index.csv
```

`users-index.csv` captures flattened JSON paths, including nested arrays.

## Run the Agent

Call the agent directly with the information you need:

```powershell
python test_data_agent\agent.py "BE customer with French language and FATCA INDSUS"
```

The agent rebuilds `users-index.csv` every time it runs, extracts requirements, searches the CSV, and returns the recommended source file.

Show selected JSON:

```powershell
python test_data_agent\agent.py "BE customer with French language and FATCA INDSUS" --show-json
```

## Manual Index Build

Usually not needed because the agent rebuilds the CSV, but available:

```powershell
python test_data_agent\build_test_data_index.py
```

Useful filters:

```text
customerID
countryOfResidence
preferredLanguage
addressCountry
taxCountry
assessmentType
assessmentResult
productType
productCurrency
```

You can also filter by full flattened JSON paths, for example:

```powershell
python test_data_agent\agent.py --filter individual.postalAddresses[0].countryCode=LU
```

