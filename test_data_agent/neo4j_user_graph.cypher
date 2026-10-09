CREATE CONSTRAINT user_customer_id IF NOT EXISTS
FOR (u:User)
REQUIRE u.customerID IS UNIQUE;

CREATE CONSTRAINT assessment_key IF NOT EXISTS
FOR (a:Assessment)
REQUIRE a.key IS UNIQUE;

CREATE CONSTRAINT product_type IF NOT EXISTS
FOR (p:Product)
REQUIRE p.type IS UNIQUE;

LOAD CSV WITH HEADERS FROM 'file:///neo4j-users.csv' AS row
MERGE (u:User {customerID: row.customerID})
SET u.sourceFile = row.sourceFile,
    u.countryOfResidence = row.countryOfResidence,
    u.preferredLanguage = row.preferredLanguage,
    u.cityOfBirth = row.cityOfBirth,
    u.gender = row.gender,
    u.maritalStatus = row.maritalStatus
MERGE (addr:Address {country: row.addressCountry, city: row.addressCity})
MERGE (u)-[:HAS_ADDRESS]->(addr)
MERGE (tax:TaxResidency {country: row.taxCountry})
MERGE (u)-[:HAS_TAX_RESIDENCY]->(tax)
MERGE (assessment:Assessment {key: row.assessmentType + '#' + row.assessmentResult})
SET assessment.type = row.assessmentType,
    assessment.resultType = row.assessmentResult
MERGE (u)-[:HAS_ASSESSMENT]->(assessment)
MERGE (product:Product {type: row.productType})
SET product.currency = row.productCurrency
MERGE (u)-[:HAS_PRODUCT]->(product);
