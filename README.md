# Generative Test Data Agent

This repository contains a GHCP-friendly test data agent that searches existing JSON test data before suggesting new synthetic data.

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

It first searches existing JSON files. If no exact match is available, it shows the closest records and explains which fields are missing or different.

## Run The Agent

From the repository root:

```powershell
python test_data_agent\agent.py "Belgian French customer with FATCA INDSUS"
```

The agent automatically refreshes the index when it is missing or stale, extracts likely requirements from your request, finds the best existing JSON, and prints the fetched test-data information.

Example with full JSON output:

```powershell
python test_data_agent\agent.py "Belgian French customer with FATCA INDSUS" --show-json
```

You can still pass exact requirements when needed:

```powershell
python test_data_agent\agent.py --filter countryOfResidence=BE --filter preferredLanguage=fr --filter assessmentResult=INDSUS
```

The indexer generates:

```text
.test-data-index/users-index.json
.test-data-index/users-index.csv
.test-data-index/users-full-flat.json
.test-data-index/users-full-flat.csv
.test-data-index/neo4j-users.csv
```

Generated index files are ignored by Git.

`users-index.csv` is a summary for common fields. `users-full-flat.csv` contains every captured JSON field using paths such as `individual.postalAddresses[0].countryCode`.

The agent returns one of:

```text
EXACT_MATCH
BEST_TEXT_MATCH
PARTIAL_MATCH
NO_MATCH
```

## Search Test Data Directly

This is optional. Prefer `agent.py` for normal usage.

Natural-language style search:

```powershell
python test_data_agent\find_test_data.py --query "Belgian French customer with FATCA INDSUS"
```

Structured filter search:

```powershell
python test_data_agent\find_test_data.py --filter countryOfResidence=BE --filter preferredLanguage=fr --filter assessmentResult=INDSUS
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

## Neo4j Option

Neo4j is optional. For a small JSON dataset, the local index is enough.

If the dataset grows and you want graph relationships, import:

```text
.test-data-index/neo4j-users.csv
```

using:

```text
test_data_agent/neo4j_user_graph.cypher
```
