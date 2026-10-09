# Generative Test Data Agent

This folder contains a local test-data finder for GHCP-assisted testing.

It indexes JSON files from:

```text
users_data/
```

and generates:

```text
.test-data-index/users-index.json
.test-data-index/users-index.csv
.test-data-index/users-full-flat.json
.test-data-index/users-full-flat.csv
.test-data-index/neo4j-users.csv
```

`users-index.csv` is the compact business-field index. `users-full-flat.csv` captures every JSON path found in the source files, including nested arrays.

## Build the Index

```powershell
python test_data_agent\build_test_data_index.py
```

## Find Test Data

Agentic selector:

```powershell
python test_data_agent\agent.py --refresh-index --request "BE customer with French language and FATCA INDSUS"
```

Natural-language search:

```powershell
python test_data_agent\find_test_data.py --query "BE customer with French language and FATCA INDSUS"
```

Structured search:

```powershell
python test_data_agent\find_test_data.py --filter countryOfResidence=BE --filter preferredLanguage=fr --filter assessmentResult=INDSUS
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

## Neo4j

Neo4j is optional. If you decide to use it later, import:

```text
.test-data-index/neo4j-users.csv
```

using:

```text
test_data_agent/neo4j_user_graph.cypher
```
