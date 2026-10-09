# Generative Test Data Agent

This repository contains a GHCP-friendly test data agent that indexes JSON test data into a CSV and searches that CSV for matching records.

The current sample data lives in:

```text
users_data/
```

The agent instructions live in:

```text
agents/generative-test-data-agent.md
.github/copilot-instructions.md
```

## What It Does

The agent helps answer questions like:

```text
Find me a Belgian customer with French language and FATCA INDSUS assessment.
Find a user with Belgian tax residency and non-Belgian address.
Find customer data with CDD result L and current account product.
```

Every time you call the agent, it rebuilds `.test-data-index/users-index.csv` from `users_data/*.json`, then uses that CSV as the input for the find job.

## Generate The CSV Mapping

From the repository root:

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
agents/generative-test-data-agent.md
```

GHCP should run the index builder, read `.test-data-index/users-index.csv`, and return the matching `sourceFile`, `caseInformation.customerID`, and matching fields.

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

