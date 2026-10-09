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

## Run The Agent

From the repository root:

```powershell
python test_data_agent\agent.py "Belgian French customer with FATCA INDSUS"
```

The agent rebuilds `.test-data-index/users-index.csv`, extracts likely requirements from your request, finds the best existing JSON, and prints the fetched test-data information.

Example with full JSON output:

```powershell
python test_data_agent\agent.py "Belgian French customer with FATCA INDSUS" --show-json
```

You can still pass exact requirements when needed:

```powershell
python test_data_agent\agent.py --filter countryOfResidence=BE --filter preferredLanguage=fr --filter assessmentResult=INDSUS
```

The main generated input file is:

```text
.test-data-index/users-index.csv
```

`users-index.csv` contains flattened JSON paths such as `individual.postalAddresses[0].countryCode`, so nested JSON fields are also available for searching.

The agent returns one of:

```text
EXACT_MATCH
BEST_TEXT_MATCH
PARTIAL_MATCH
NO_MATCH
```

Common filters:

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

