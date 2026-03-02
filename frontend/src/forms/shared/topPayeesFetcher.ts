import { query } from '../../api';
import type { FilingScope } from '../../utils/filingScope';
import { filingScopeWhere, filingScopeUrlParams } from '../../utils/filingScope';

export interface TopPayee {
  payee: string;
  payee_organization_name: string | null;
  payee_last_name: string | null;
  total_amount: number;
  purposes: string;
}

export function fetchTopPayees(
  dbName: string,
  scope: FilingScope,
  scheduleFormType: string
): Promise<TopPayee[]> {
  const { where, params } = filingScopeWhere(scope);

  const sql = `
    SELECT
      COALESCE(NULLIF(payee_organization_name, ''), payee_last_name || COALESCE(', ' || payee_first_name, '')) as payee,
      payee_organization_name,
      payee_last_name,
      SUM(expenditure_amount) as total_amount,
      GROUP_CONCAT(DISTINCT expenditure_purpose_descrip) as purposes
    FROM libfec_schedule_b
    WHERE
      ${where}
      AND form_type = '${scheduleFormType}'
      AND memo_code != 'X'
    GROUP BY payee
    ORDER BY total_amount DESC
    LIMIT 20
  `;
  return query(dbName, sql, params);
}

export function buildPayeeUrl(
  dbName: string,
  scope: FilingScope,
  row: TopPayee,
  scheduleFormType: string,
  filingIds?: string[]
): string {
  const scopeParams = filingScopeUrlParams(scope, filingIds);
  const params = new URLSearchParams({
    _sort: 'rowid',
    ...scopeParams,
    form_type__exact: scheduleFormType,
  });
  if (row.payee_organization_name) {
    params.set('payee_organization_name__exact', row.payee_organization_name);
  } else if (row.payee_last_name) {
    params.set('payee_last_name__exact', row.payee_last_name);
  }
  return `/${dbName}/libfec_schedule_b?${params}`;
}
