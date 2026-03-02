import { query } from '../../api';
import type { FilingScope } from '../../utils/filingScope';
import { filingScopeWhere, filingScopeUrlParams } from '../../utils/filingScope';

export interface StateContribution {
  contributor_state: string;
  total_contributions: number;
}

export interface ScopeMetadata {
  committee_name: string | null;
  coverage_from_date: string | null;
  coverage_through_date: string | null;
  form_type: string | null;
}

export async function fetchScopeMetadata(
  dbName: string,
  scope: FilingScope
): Promise<ScopeMetadata> {
  const { where, params } = filingScopeWhere(scope);

  const sql = `
    SELECT
      MAX(filer_name) as committee_name,
      MIN(coverage_from_date) as coverage_from_date,
      MAX(coverage_through_date) as coverage_through_date,
      MAX(cover_record_form) as form_type
    FROM libfec_filings
    WHERE ${where}
  `;
  const rows = await query(dbName, sql, params);
  return (
    (rows as ScopeMetadata[])[0] ?? {
      committee_name: null,
      coverage_from_date: null,
      coverage_through_date: null,
      form_type: null,
    }
  );
}

export function fetchStateContributions(
  dbName: string,
  scope: FilingScope
): Promise<StateContribution[]> {
  const { where, params } = filingScopeWhere(scope);

  const sql = `
    SELECT
      contributor_state,
      SUM(contribution_amount) as total_contributions
    FROM libfec_schedule_a
    WHERE ${where}
      AND contributor_state IS NOT NULL
      AND contributor_state != ''
      AND memo_code != 'X'
    GROUP BY contributor_state
    ORDER BY total_contributions DESC
  `;
  return query(dbName, sql, params);
}

export function buildStateUrl(
  dbName: string,
  scope: FilingScope,
  stateCode: string,
  formTypeFilter?: string,
  filingIds?: string[]
): string {
  const scopeParams = filingScopeUrlParams(scope, filingIds);
  const params = new URLSearchParams({
    _sort: 'rowid',
    contributor_state__exact: stateCode,
    ...scopeParams,
    memo_code__not: 'X',
  });
  if (formTypeFilter) {
    params.set('form_type__exact', formTypeFilter);
  }
  return `/${dbName}/libfec_schedule_a?${params}`;
}
