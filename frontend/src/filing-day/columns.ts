/**
 * Column definitions for the Filing Day comparison table.
 * Maps user-friendly column names to F3 database fields.
 */

export type ColumnCategory = 'receipts' | 'disbursements' | 'balance';

export interface ColumnDef {
  id: string;
  label: string;
  shortLabel: string;
  // SQL expression - can reference f3.* columns
  sqlExpr: string;
  // Whether this is a currency column (for formatting)
  isCurrency: boolean;
  // Whether this is a percentage/ratio column
  isPercent?: boolean;
  // Description for tooltip
  description: string;
  // Category for grouping in selector
  category: ColumnCategory;
}

export const AVAILABLE_COLUMNS: ColumnDef[] = [
  // Receipts
  {
    id: 'total_individual',
    label: 'Total Individual Contributions',
    shortLabel: 'Total Indiv.',
    sqlExpr: 'f3.col_a_total_individual_contributions',
    isCurrency: true,
    description: 'Total contributions from individuals (itemized + unitemized)',
    category: 'receipts',
  },
  {
    id: 'large_individual',
    label: 'Large Individual (Itemized)',
    shortLabel: 'Large Indiv.',
    sqlExpr: 'f3.col_a_individual_contributions_itemized',
    isCurrency: true,
    description: 'Itemized individual contributions (over $200)',
    category: 'receipts',
  },
  {
    id: 'small_individual',
    label: 'Small Individual (Unitemized)',
    shortLabel: 'Small Indiv.',
    sqlExpr: 'f3.col_a_individual_contributions_unitemized',
    isCurrency: true,
    description: 'Unitemized individual contributions ($200 or less)',
    category: 'receipts',
  },
  {
    id: 'small_donor_ratio',
    label: 'Small Donor Ratio',
    shortLabel: 'Small %',
    sqlExpr:
      'CASE WHEN f3.col_a_total_individual_contributions > 0 THEN f3.col_a_individual_contributions_unitemized * 100.0 / f3.col_a_total_individual_contributions ELSE NULL END',
    isCurrency: false,
    isPercent: true,
    description: 'Percentage of individual donations from small donors',
    category: 'receipts',
  },
  {
    id: 'candidate_loans',
    label: 'Candidate Loans',
    shortLabel: 'Cand. Loans',
    sqlExpr: 'f3.col_a_candidate_loans',
    isCurrency: true,
    description: 'Loans from the candidate to their campaign',
    category: 'receipts',
  },
  {
    id: 'pac_contributions',
    label: 'PAC Contributions',
    shortLabel: 'PAC',
    sqlExpr: 'f3.col_a_pac_contributions',
    isCurrency: true,
    description: 'Contributions from Political Action Committees',
    category: 'receipts',
  },
  {
    id: 'party_contributions',
    label: 'Party Contributions',
    shortLabel: 'Party',
    sqlExpr: 'f3.col_a_political_party_contributions',
    isCurrency: true,
    description: 'Contributions from political party committees',
    category: 'receipts',
  },
  {
    id: 'total_receipts',
    label: 'Total Receipts',
    shortLabel: 'Receipts',
    sqlExpr: 'f3.col_a_total_receipts',
    isCurrency: true,
    description: 'Total receipts for the period',
    category: 'receipts',
  },
  // Disbursements
  {
    id: 'operating_expenditures',
    label: 'Operating Expenditures',
    shortLabel: 'Op. Exp.',
    sqlExpr: 'f3.col_a_operating_expenditures',
    isCurrency: true,
    description: 'Total operating expenditures for the period',
    category: 'disbursements',
  },
  {
    id: 'total_refunds',
    label: 'Total Refunds',
    shortLabel: 'Refunds',
    sqlExpr: 'f3.col_a_total_refunds',
    isCurrency: true,
    description: 'Total contribution refunds issued',
    category: 'disbursements',
  },
  {
    id: 'total_disbursements',
    label: 'Total Disbursements',
    shortLabel: 'Disbursements',
    sqlExpr: 'f3.col_a_total_disbursements',
    isCurrency: true,
    description: 'Total disbursements for the period',
    category: 'disbursements',
  },
  // Cash on Hand
  {
    id: 'cash_on_hand_begin',
    label: 'Cash on Hand (Beginning)',
    shortLabel: 'COH Begin',
    sqlExpr: 'f3.col_a_cash_beginning_reporting_period',
    isCurrency: true,
    description: 'Cash on hand at beginning of reporting period',
    category: 'balance',
  },
  {
    id: 'cash_on_hand_end',
    label: 'Cash on Hand (End)',
    shortLabel: 'COH End',
    sqlExpr: 'f3.col_a_cash_on_hand_close_of_period',
    isCurrency: true,
    description: 'Cash on hand at close of reporting period',
    category: 'balance',
  },
];

export const DEFAULT_COLUMNS = ['total_individual', 'operating_expenditures', 'cash_on_hand_end'];

export function getColumnById(id: string): ColumnDef | undefined {
  return AVAILABLE_COLUMNS.find((c) => c.id === id);
}

export function getColumnsById(ids: string[]): ColumnDef[] {
  return ids.map((id) => getColumnById(id)).filter((c): c is ColumnDef => c !== undefined);
}

export function getColumnsByCategory(category: ColumnCategory): ColumnDef[] {
  return AVAILABLE_COLUMNS.filter((c) => c.category === category);
}
