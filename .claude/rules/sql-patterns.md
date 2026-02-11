# SQL Patterns

## CTE Standard (DBT Style)

When writing SQL with CTEs, follow the DBT convention:
- Name the last CTE `final`
- The main query should be just `SELECT * FROM final`

```sql
WITH source_data AS (
  SELECT * FROM some_table WHERE ...
),
transformed AS (
  SELECT ... FROM source_data
),
final AS (
  SELECT ... FROM transformed
  ORDER BY ...
  LIMIT ...
)
SELECT * FROM final
```

This makes queries easier to debug (you can change the final SELECT to query intermediate CTEs) and provides a consistent structure.

## Common Tables

- `libfec_candidates` - Candidate records with `candidate_id`, `name`, `party_affiliation`, `state`, `office`, `district`, `incumbent_challenger_status`, `principal_campaign_committee`, `cycle`
- `libfec_committees` - Committee records with `committee_id`, `name`, `committee_type`, `designation`, `candidate_id`, `cycle`
- `libfec_filings` - Filing metadata with `filing_id`, `filer_id`, `filer_name`, `cover_record_form`, `coverage_from_date`, `coverage_through_date`
- `libfec_F3` - Form F3 data (campaign finance reports) with financial columns like `col_a_total_receipts`, `col_a_cash_on_hand_close_of_period`, `report_code`, `coverage_through_date`

## Join Patterns

### Candidate to Filing (via Committee)
```sql
SELECT c.*, f3.*
FROM libfec_candidates c
JOIN libfec_filings fil ON c.principal_campaign_committee = fil.filer_id
JOIN libfec_F3 f3 ON fil.filing_id = f3.filing_id
```

### Filing to Form Data
```sql
SELECT fil.*, f3.*
FROM libfec_filings fil
JOIN libfec_F3 f3 ON fil.filing_id = f3.filing_id
WHERE fil.filing_id = :filing_id
```

## CTEs for Complex Queries

Use CTEs to separate filtering logic from joins:
```sql
WITH matching_filings AS (
  SELECT fil.filer_id, f3.*
  FROM libfec_filings fil
  JOIN libfec_F3 f3 ON fil.filing_id = f3.filing_id
  WHERE f3.report_code = :report_code
),
candidates_in_race AS (
  SELECT * FROM libfec_candidates
  WHERE office = :office AND state = :state
)
SELECT c.*, mf.*
FROM candidates_in_race c
JOIN matching_filings mf ON c.principal_campaign_committee = mf.filer_id
```

## Date Filtering

Use `strftime` for year extraction:
```sql
WHERE strftime('%Y', f3.coverage_through_date) = :year
```

## Parameter Syntax

Use `:name` syntax for parameters (Datasette convention):
```sql
WHERE candidate_id = :candidate_id AND cycle = :cycle
```
