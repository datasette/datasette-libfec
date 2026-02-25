import * as d3 from 'd3';
import { SankeyChart } from './base_sankey';

const groupColors = {
  'individual-item': '#97bbf5',
  individuals: '#97bbf5',
  contributions: '#6cc5b0',
  receipts: '#3ca951',
  'receipt-other': '#a463f2',
  nonfederal: '#ff8ab7',
  disburse: '#efb118',
  'operating-detail': '#ff725c',
  'fea-detail': '#9c6b4e',
  coh: '#9498a0',
};

export interface F3XInputRow {
  coverage_from_date: string;
  coverage_through_date: string;
  col_a_cash_on_hand_beginning_period: number;
  col_a_cash_on_hand_close_of_period: number;

  // Receipts
  col_a_individuals_itemized: number;
  col_a_individuals_unitemized: number;
  col_a_individual_contribution_total: number;
  col_a_political_party_committees: number;
  col_a_other_political_committees_pacs: number;
  col_a_total_contributions: number;
  col_a_transfers_from_aff_other_party_cmttees: number;
  col_a_total_loans: number;
  col_a_total_loan_repayments_received: number;
  col_a_offsets_to_expenditures: number;
  col_a_federal_refunds: number;
  col_a_other_federal_receipts: number;
  col_a_transfers_from_nonfederal_h3: number;
  col_a_levin_funds: number;
  col_a_total_nonfederal_transfers: number;
  col_a_total_receipts: number;

  // Disbursements
  col_a_shared_operating_expenditures_federal: number;
  col_a_shared_operating_expenditures_nonfederal: number;
  col_a_other_federal_operating_expenditures: number;
  col_a_total_operating_expenditures: number;
  col_a_transfers_to_affiliated: number;
  col_a_contributions_to_candidates: number;
  col_a_independent_expenditures: number;
  col_a_coordinated_expenditures_by_party_committees: number;
  col_a_total_loan_repayments_made: number;
  col_a_loans_made: number;
  col_a_refunds_to_individuals: number;
  col_a_refunds_to_party_committees: number;
  col_a_refunds_to_other_committees: number;
  col_a_total_refunds: number;
  col_a_other_disbursements: number;
  col_a_federal_election_activity_federal_share: number;
  col_a_federal_election_activity_levin_share: number;
  col_a_federal_election_activity_all_federal: number;
  col_a_federal_election_activity_total: number;
}

export interface F3XNode {
  id: keyof F3XInputRow;
  label: string;
  to?: keyof F3XInputRow;
  from?: keyof F3XInputRow;
  group: keyof typeof groupColors;
  schedule: null | 'A' | 'B' | 'D' | 'E' | 'H3' | 'H4' | 'H6';
  line_number: null | string;
  clickable: boolean;
  value?: (data: F3XInputRow[]) => number;
}

const f3x_nodes: F3XNode[] = [
  // ── Receipts ──────────────────────────────────────────────────

  // Individual contributions breakdown
  {
    id: 'col_a_individuals_itemized',
    label: 'Large Donors',
    to: 'col_a_individual_contribution_total',
    group: 'individual-item',
    line_number: '11AI',
    schedule: 'A',
    clickable: true,
  },
  {
    id: 'col_a_individuals_unitemized',
    label: 'Small Donors',
    to: 'col_a_individual_contribution_total',
    group: 'individual-item',
    line_number: '11AII',
    schedule: 'A',
    clickable: false,
  },
  {
    id: 'col_a_individual_contribution_total',
    label: 'Individuals',
    to: 'col_a_total_receipts',
    group: 'individuals',
    line_number: '11AIII',
    schedule: 'A',
    clickable: false,
  },

  // Other contributions → total receipts
  {
    id: 'col_a_political_party_committees',
    label: 'Political Party',
    to: 'col_a_total_receipts',
    group: 'contributions',
    line_number: '11B',
    schedule: 'A',
    clickable: true,
  },
  {
    id: 'col_a_other_political_committees_pacs',
    label: 'Other PACs',
    to: 'col_a_total_receipts',
    group: 'contributions',
    line_number: '11C',
    schedule: 'A',
    clickable: true,
  },

  // Other receipt items → total receipts
  {
    id: 'col_a_transfers_from_aff_other_party_cmttees',
    label: 'Transfers In',
    to: 'col_a_total_receipts',
    group: 'receipt-other',
    line_number: '12',
    schedule: 'A',
    clickable: true,
  },
  {
    id: 'col_a_total_loans',
    label: 'Loans Received',
    to: 'col_a_total_receipts',
    group: 'receipt-other',
    line_number: '13',
    schedule: 'A',
    clickable: true,
  },
  {
    id: 'col_a_total_loan_repayments_received',
    label: 'Loan Repayments Received',
    to: 'col_a_total_receipts',
    group: 'receipt-other',
    line_number: '14',
    schedule: 'A',
    clickable: true,
  },
  {
    id: 'col_a_offsets_to_expenditures',
    label: 'Expenditure Offsets',
    to: 'col_a_total_receipts',
    group: 'receipt-other',
    line_number: '15',
    schedule: 'A',
    clickable: true,
  },
  {
    id: 'col_a_federal_refunds',
    label: 'Federal Refunds',
    to: 'col_a_total_receipts',
    group: 'receipt-other',
    line_number: '16',
    schedule: 'A',
    clickable: true,
  },
  {
    id: 'col_a_other_federal_receipts',
    label: 'Other Federal Receipts',
    to: 'col_a_total_receipts',
    group: 'receipt-other',
    line_number: '17',
    schedule: 'A',
    clickable: true,
  },

  // Nonfederal transfers breakdown → total nonfederal → total receipts
  {
    id: 'col_a_transfers_from_nonfederal_h3',
    label: 'Nonfederal Transfers',
    to: 'col_a_total_nonfederal_transfers',
    group: 'nonfederal',
    line_number: '18A',
    schedule: 'H3',
    clickable: true,
  },
  {
    id: 'col_a_levin_funds',
    label: 'Levin Funds',
    to: 'col_a_total_nonfederal_transfers',
    group: 'nonfederal',
    line_number: '18B',
    schedule: 'A',
    clickable: true,
  },
  {
    id: 'col_a_total_nonfederal_transfers',
    label: 'Nonfederal Transfers',
    to: 'col_a_total_receipts',
    group: 'nonfederal',
    line_number: '18C',
    schedule: null,
    clickable: false,
  },

  // Central receipts node
  {
    id: 'col_a_total_receipts',
    label: 'Available Funds',
    group: 'receipts',
    line_number: '19',
    schedule: null,
    clickable: false,
  },

  // ── Disbursements ─────────────────────────────────────────────

  // Operating expenditures breakdown
  {
    id: 'col_a_shared_operating_expenditures_federal',
    label: 'Shared Federal',
    from: 'col_a_total_operating_expenditures',
    group: 'operating-detail',
    line_number: '21AI',
    schedule: 'H4',
    clickable: true,
  },
  {
    id: 'col_a_shared_operating_expenditures_nonfederal',
    label: 'Shared Nonfederal',
    from: 'col_a_total_operating_expenditures',
    group: 'operating-detail',
    line_number: '21AII',
    schedule: 'H4',
    clickable: true,
  },
  {
    id: 'col_a_other_federal_operating_expenditures',
    label: 'Other Federal Operating',
    from: 'col_a_total_operating_expenditures',
    group: 'operating-detail',
    line_number: '21B',
    schedule: 'B',
    clickable: true,
  },
  {
    id: 'col_a_total_operating_expenditures',
    label: 'Operating Expenses',
    from: 'col_a_total_receipts',
    group: 'disburse',
    line_number: '21C',
    schedule: null,
    clickable: false,
  },

  // Direct disbursements
  {
    id: 'col_a_transfers_to_affiliated',
    label: 'Transfers Out',
    from: 'col_a_total_receipts',
    group: 'disburse',
    line_number: '22',
    schedule: 'B',
    clickable: true,
  },
  {
    id: 'col_a_contributions_to_candidates',
    label: 'Contributions to Candidates',
    from: 'col_a_total_receipts',
    group: 'disburse',
    line_number: '23',
    schedule: 'B',
    clickable: true,
  },
  {
    id: 'col_a_independent_expenditures',
    label: 'Independent Expenditures',
    from: 'col_a_total_receipts',
    group: 'disburse',
    line_number: '24',
    schedule: 'E',
    clickable: true,
  },
  {
    id: 'col_a_coordinated_expenditures_by_party_committees',
    label: 'Coordinated Expenditures',
    from: 'col_a_total_receipts',
    group: 'disburse',
    line_number: '25',
    schedule: 'B',
    clickable: true,
  },
  {
    id: 'col_a_total_loan_repayments_made',
    label: 'Loan Repayments',
    from: 'col_a_total_receipts',
    group: 'disburse',
    line_number: '26',
    schedule: 'B',
    clickable: true,
  },
  {
    id: 'col_a_loans_made',
    label: 'Loans Made',
    from: 'col_a_total_receipts',
    group: 'disburse',
    line_number: '27',
    schedule: 'B',
    clickable: true,
  },

  // Refunds breakdown
  {
    id: 'col_a_refunds_to_individuals',
    label: 'to Individuals',
    from: 'col_a_total_refunds',
    group: 'disburse',
    line_number: '28A',
    schedule: 'B',
    clickable: true,
  },
  {
    id: 'col_a_refunds_to_party_committees',
    label: 'to Party Committees',
    from: 'col_a_total_refunds',
    group: 'disburse',
    line_number: '28B',
    schedule: 'B',
    clickable: true,
  },
  {
    id: 'col_a_refunds_to_other_committees',
    label: 'to Other Committees',
    from: 'col_a_total_refunds',
    group: 'disburse',
    line_number: '28C',
    schedule: 'B',
    clickable: true,
  },
  {
    id: 'col_a_total_refunds',
    label: 'Refunds',
    from: 'col_a_total_receipts',
    group: 'disburse',
    line_number: '28D',
    schedule: null,
    clickable: false,
  },

  {
    id: 'col_a_other_disbursements',
    label: 'Other Disbursements',
    from: 'col_a_total_receipts',
    group: 'disburse',
    line_number: '29',
    schedule: 'B',
    clickable: true,
  },

  // Federal Election Activity breakdown
  {
    id: 'col_a_federal_election_activity_federal_share',
    label: 'FEA Federal Share',
    from: 'col_a_federal_election_activity_total',
    group: 'fea-detail',
    line_number: '30AI',
    schedule: 'H6',
    clickable: true,
  },
  {
    id: 'col_a_federal_election_activity_levin_share',
    label: 'FEA Levin Share',
    from: 'col_a_federal_election_activity_total',
    group: 'fea-detail',
    line_number: '30AII',
    schedule: 'H6',
    clickable: true,
  },
  {
    id: 'col_a_federal_election_activity_all_federal',
    label: 'FEA All Federal',
    from: 'col_a_federal_election_activity_total',
    group: 'fea-detail',
    line_number: '30B',
    schedule: 'B',
    clickable: true,
  },
  {
    id: 'col_a_federal_election_activity_total',
    label: 'Federal Election Activity',
    from: 'col_a_total_receipts',
    group: 'disburse',
    line_number: '30C',
    schedule: null,
    clickable: false,
  },

  // ── Cash on Hand ──────────────────────────────────────────────
  {
    id: 'col_a_cash_on_hand_beginning_period',
    label: 'Cash on Hand',
    to: 'col_a_total_receipts',
    group: 'coh',
    line_number: null,
    schedule: null,
    clickable: false,
    value: (data: F3XInputRow[]) => {
      const idx = d3.minIndex(data, (d) => d.coverage_from_date);
      const row = idx >= 0 ? data[idx] : undefined;
      return row?.col_a_cash_on_hand_beginning_period ?? 0;
    },
  },
  {
    id: 'col_a_cash_on_hand_close_of_period',
    label: 'Cash on Hand End',
    from: 'col_a_total_receipts',
    group: 'coh',
    line_number: null,
    schedule: null,
    clickable: false,
    value: (data: F3XInputRow[]) => {
      const idx = d3.maxIndex(data, (d) => d.coverage_through_date);
      const row = idx >= 0 ? data[idx] : undefined;
      return row?.col_a_cash_on_hand_close_of_period ?? 0;
    },
  },
];

export function F3XSankey(
  data: F3XInputRow[],
  params: { width: number; onClick?: (d: F3XNode) => void; showCoh: boolean }
): SVGSVGElement {
  const { width, onClick, showCoh } = params;
  const links = f3x_nodes
    .filter(showCoh ? () => true : (n) => n.group !== 'coh')
    .flatMap((n) =>
      n.from || n.to
        ? [
            {
              id: n.id,
              source: n.from ? n.from : n.id,
              target: n.to ? n.to : n.id,
              label: n.label,
              value: n.value ? n.value(data) : d3.sum(data, (d) => d[n.id] as number),
            },
          ]
        : []
    )
    .filter((d) => d.value > 0);

  // If only one source feeds into "Individuals", bypass the intermediate node
  const individualsId = 'col_a_individual_contribution_total';
  const inbound = links.filter((l) => l.target === individualsId);
  if (inbound.length === 1 && inbound[0]) {
    // Point the single inbound link directly to total_receipts
    inbound[0].target = 'col_a_total_receipts' as keyof F3XInputRow;
    // Remove the outbound link from Individuals → total_receipts
    const outIdx = links.findIndex((l) => l.source === individualsId);
    if (outIdx >= 0) links.splice(outIdx, 1);
  }

  const nodes = f3x_nodes
    .map((d) => ({ id: d.id, label: d.label }))
    .filter((d) => links.some((l) => l.source === d.id || l.target === d.id));

  const $ = d3.format('$.3s');

  return SankeyChart(
    { nodes, links },
    {
      width,
      height: (width * 3) / 4,
      nodeGroup: (d) => f3x_nodes.find((d2) => d.id === d2.id)?.group,
      nodeGroups: Object.keys(groupColors),
      colors: Object.values(groupColors),
      nodeAlign: 'justify',
      linkColor: 'source-target',
      nodeWidth: 10,
      nodeClickable: (d) => f3x_nodes.find((d2) => d.id === d2.id)?.clickable ?? false,
      nodeLabel: (d) => {
        const { label } = f3x_nodes.find((d2) => d.id === d2.id)!;
        return [$(d.value), label];
      },
      nodeTitle: (d) => {
        const { schedule, line_number } = f3x_nodes.find((d2) => d.id === d2.id)!;
        return `${schedule}${line_number}`;
      },
      format: (d) => $(d),
      onClick: onClick ? (d) => onClick(f3x_nodes.find((d2) => d.id === d2.id)!) : undefined,
    }
  );
}
