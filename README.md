# Generative Test Data Agent

This repository contains GHCP-friendly test data workflows:

- Find existing test data by indexing JSON into a CSV.
- Create similar test data by cloning an existing JSON structure and applying requested field changes.

The current sample data lives in:

```text
users_data/
```

The agent instructions live in:

```text
agents/generative-test-data-finder-agent.md
.github/copilot-instructions.md
```

## What It Does

The finder flow helps answer questions like:

```text
Find me a Belgian customer with French language and FATCA INDSUS assessment.
Find a user with Belgian tax residency and non-Belgian address.
Find customer data with CDD result L and current account product.
```

The normal finder flow uses `.test-data-index/users-index.csv` as the prepared input. Rebuild it only when you add or change JSON data.

The creator flow helps with requests like:

```text
Create similar data from users2.json but make country of tax residence LU.
Create a new BE customer based on the closest CDD L customer but change preferred language to fr.
```

## Generate The CSV Mapping

Run this only when the JSON test data changes or when you want to refresh the CSV:

```powershell
python test_data_agent\build_test_data_index.py
```

The main generated input file is:

```text
.test-data-index/users-index.csv
```

`users-index.csv` contains flattened JSON paths such as `individual.postalAddresses[0].countryCode`, so nested JSON fields are also available for searching.

## GHCP Usage

In GitHub Copilot Chat, ask questions such as:

```text
Using the Generative Test Data Agent, find test data for a BE customer with French language and FATCA INDSUS.
```

GHCP should follow:

```text
.github/copilot-instructions.md
```

and use:

```text
agents/generative-test-data-finder-agent.md
agents/generative-test-data-creator-agent.md
```

GHCP should read `.test-data-index/users-index.csv` and return the matching `sourceFile`, `caseInformation.customerID`, and matching fields. `sourceFile` is a repository-relative path such as `users_data/users2.json`.

GHCP should match the user's request against the flattened columns. Return the matching source JSON and customer ID.

Output:
Write the result report by running this PowerShell command. Replace `<result text>` with the final answer content:

```powershell
$reportPath = "runtime/data-finder--report.txt"
$reportContent = @'
<result text>
'@
New-Item -ItemType Directory -Force -Path (Split-Path $reportPath) | Out-Null
Set-Content -Path $reportPath -Value $reportContent -Encoding UTF8
if (-not (Test-Path $reportPath)) { throw "Report was not created: $reportPath" }
```

For creating new test data, GHCP should use:

```powershell
python test_data_agent\create_test_data_from_template.py --template users_data\<sourceFile> --output generated_data\<newFile>.json --set <json.path>=<value>
```

Example:

```powershell
python test_data_agent\create_test_data_from_template.py --template users_data\users2.json --output generated_data\users2_tax_lu.json --set taxResidencies[0].countryOfTaxResidence=LU
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
```

