export type FilingScope =
  | { mode: 'single'; filingId: string }
  | {
      mode: 'committee';
      committeeId: string;
      formType: 'F3' | 'F3X';
      cycle: number;
    };

/**
 * Returns a SQL WHERE clause fragment and params for filtering by filing scope.
 * Single mode: WHERE filing_id = :filing_id
 * Committee mode: WHERE filing_id IN (subquery excluding superseded filings)
 */
export function filingScopeWhere(scope: FilingScope): {
  where: string;
  params: Record<string, string>;
} {
  if (scope.mode === 'single') {
    return {
      where: 'filing_id = :filing_id',
      params: { filing_id: scope.filingId },
    };
  }

  const year1 = String(scope.cycle - 1);
  const year2 = String(scope.cycle);

  return {
    where: `filing_id IN (
      SELECT af.filing_id
      FROM libfec_filings af
      WHERE af.filer_id = :committee_id
        AND af.cover_record_form = :form_type
        AND strftime('%Y', af.coverage_through_date) IN (:year1, :year2)
        AND af.filing_id NOT IN (
          SELECT substr(af2.report_id, 5)
          FROM libfec_filings af2
          WHERE af2.filer_id = :committee_id
            AND af2.cover_record_form = :form_type
            AND strftime('%Y', af2.coverage_through_date) IN (:year1, :year2)
            AND af2.report_id LIKE 'FEC-%'
        )
    )`,
    params: {
      committee_id: scope.committeeId,
      form_type: scope.formType,
      year1,
      year2,
    },
  };
}

/**
 * Returns URL search params for linking to datasette table views.
 * Single mode: filing_id__exact
 * Committee mode: filing_id__in with resolved filing IDs
 */
export function filingScopeUrlParams(
  scope: FilingScope,
  filingIds?: string[]
): Record<string, string> {
  if (scope.mode === 'single') {
    return { filing_id__exact: scope.filingId };
  }
  if (filingIds && filingIds.length > 0) {
    return { filing_id__in: filingIds.join(',') };
  }
  return { filer_committee_id_number__exact: scope.committeeId };
}

/**
 * Resolves the actual filing IDs for a scope by querying the database.
 * Single mode: returns [filingId]
 * Committee mode: runs the non-superseded filings subquery
 */
export async function fetchFilingIds(
  dbName: string,
  scope: FilingScope,
  queryFn: (
    db: string,
    sql: string,
    params?: Record<string, string>
  ) => Promise<{ filing_id: string }[]>
): Promise<string[]> {
  if (scope.mode === 'single') {
    return [scope.filingId];
  }

  const { where, params } = filingScopeWhere(scope);
  const sql = `SELECT filing_id FROM libfec_filings WHERE ${where}`;
  const rows = await queryFn(dbName, sql, params);
  return rows.map((r) => String(r.filing_id));
}
