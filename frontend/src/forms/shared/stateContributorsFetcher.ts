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

/**
 * Schedule A rows that represent contributions from individuals, matching how
 * FEC.gov builds its by-state breakdown:
 * - Line 11(a)(i) itemized individual contributions (non-memo). Earmarked
 *   contributions (e.g. via WinRed) are itemized here under the donor; the
 *   conduit's own "earmarked-conduit details" rows are memo entries.
 * - Line 12 memo entries for individuals (and tribes, which FEC also counts):
 *   the donors behind joint fundraising committee transfers. The non-memo line
 *   12 row is the transfer from the JFC itself, which would otherwise be
 *   attributed to the JFC's state.
 *
 * Partnership/LLC contributions are counted once, via the non-memo 11(a)(i)
 * row; the memo attributions to individual partners are skipped.
 */
export const INDIVIDUAL_CONTRIBUTIONS_WHERE = `(
  (form_type = 'SA11AI' AND memo_code IS NOT 'X')
  OR (form_type = 'SA12' AND memo_code = 'X' AND entity_type IN ('IND', 'ORG'))
)`;

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
      AND ${INDIVIDUAL_CONTRIBUTIONS_WHERE}
    GROUP BY contributor_state
    ORDER BY total_contributions DESC
  `;
  return query(dbName, sql, params);
}

export function buildStateUrl(
  dbName: string,
  scope: FilingScope,
  stateCode: string,
  filingIds?: string[]
): string {
  const scopeParams = filingScopeUrlParams(scope, filingIds);
  const params = new URLSearchParams({
    _sort: 'rowid',
    contributor_state__exact: stateCode,
    ...scopeParams,
    _where: INDIVIDUAL_CONTRIBUTIONS_WHERE.replace(/\s+/g, ' ').trim(),
  });
  return `/${dbName}/libfec_schedule_a?${params}`;
}
