import { query } from '../../api';
import type { FilingScope } from '../../utils/filingScope';
import { filingScopeWhere, filingScopeUrlParams } from '../../utils/filingScope';

export interface StateContribution {
  contributor_state: string;
  total_contributions: number;
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
  formTypeFilter?: string
): string {
  const scopeParams = filingScopeUrlParams(scope);
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
