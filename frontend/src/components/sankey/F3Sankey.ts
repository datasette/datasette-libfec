import * as d3 from 'd3';
import { SankeyChart } from './base_sankey';

const groupColors = {
	'individual-item': '#97bbf5',
	individuals: '#97bbf5', //"#4269d0",
	receipts: '#3ca951',
	'receipt-other': '#6cc5b0',
	disburse: '#efb118',
  coh: '#9498a0'
};
// ["#4269d0","#efb118","#ff725c","#6cc5b0","#3ca951","#ff8ab7","#a463f2","#97bbf5","#9c6b4e","#9498a0"]

export interface InputRow {
  coverage_from_date: string;
  coverage_through_date: string;
  col_a_cash_beginning_reporting_period: number;
  col_a_cash_on_hand_close_of_period: number;

	col_a_individual_contributions_itemized: number;
	col_a_individual_contributions_unitemized: number;
  col_a_political_party_contributions: number;
	col_a_total_individual_contributions: number;
	col_a_total_receipts: number;
	col_a_pac_contributions: number;
	col_a_candidate_contributions: number;
	col_a_transfers_from_authorized: number;
	col_a_candidate_loans: number;
	col_a_other_loans: number;
	col_a_offset_to_operating_expenditures: number;
	col_a_other_receipts: number;
	col_a_operating_expenditures: number;
	col_a_transfers_to_authorized: number;
	col_a_total_loan_repayments: number;
	col_a_candidate_loan_repayments: number;
	col_a_other_loan_repayments: number;
	col_a_total_refunds: number;
	col_a_refunds_to_individuals: number;
	col_a_refunds_to_party_committees: number;
	col_a_refunds_to_other_committees: number;
	col_a_other_disbursements: number;
}

interface F3Node {
	id: keyof InputRow;
	label: string;
	to?: keyof InputRow;
	from?: keyof InputRow;
	group: keyof typeof groupColors;
	schedule: null | 'A' | 'B' | 'D';
	line_number: null | string;
  value?: (data: InputRow[]) => number;
}

const f3_nodes: F3Node[] = [
	{
		id: 'col_a_individual_contributions_itemized',
		label: 'Large Donors',
		to: 'col_a_total_individual_contributions',
		group: 'individual-item',
		line_number: '11AI',
		schedule: 'A'
	},
	{
		id: 'col_a_individual_contributions_unitemized',
		label: 'Small Donors',
		to: 'col_a_total_individual_contributions',
		group: 'individual-item',
		line_number: '11AII',
		schedule: 'A'
	},
	{
		id: 'col_a_total_individual_contributions',
		to: 'col_a_total_receipts',
		label: 'Individuals',
		group: 'individuals',
		line_number: '11AIII',
		schedule: 'A'
	},

	{

		id: 'col_a_political_party_contributions',
		label: 'Political Party Contributions',
		to: 'col_a_total_receipts',
		group: 'receipt-other',
		line_number: '11B',
		schedule: 'A'
	},
	{
		id: 'col_a_pac_contributions',
		label: 'PAC Contributions',
		to: 'col_a_total_receipts',
		group: 'receipt-other',
		line_number: '11C',
		schedule: 'A'
	},
	{
		id: 'col_a_candidate_contributions',
		label: 'Candidate',
		to: 'col_a_total_receipts',
		group: 'receipt-other',
		line_number: '11D',
		schedule: 'A'
	},
	{
		id: 'col_a_transfers_from_authorized',
		label: 'Authorized Transfers',
		to: 'col_a_total_receipts',
		group: 'receipt-other',
		line_number: '12',
		schedule: 'A'
	},
	{
		id: 'col_a_candidate_loans',
		label: 'Candidate Loans',
		to: 'col_a_total_receipts',
		group: 'receipt-other',
		line_number: '13A',
		schedule: 'A'
	},
	{
		id: 'col_a_other_loans',
		label: 'Other Loans',
		to: 'col_a_total_receipts',
		group: 'receipt-other',
		line_number: '13B',
		schedule: 'A'
	},
	{
		id: 'col_a_offset_to_operating_expenditures',
		label: 'Expenditure Offsets',
		to: 'col_a_total_receipts',
		group: 'receipt-other',
		line_number: '14',
		schedule: 'A'
	},
	{
		id: 'col_a_other_receipts',
		label: 'Other',
		to: 'col_a_total_receipts',
		group: 'receipt-other',
		line_number: '15',
		schedule: 'A'
	},
	{
		id: 'col_a_total_receipts',
		label: 'Available Funds', //'Receipts',
		group: 'receipts',
		line_number: '16',
		schedule: 'A'
	},
	{
		id: 'col_a_operating_expenditures',
		label: 'Operating Expenses',
		from: 'col_a_total_receipts',
		group: 'disburse',
		line_number: '17',
		schedule: 'B'
	},
	{
		id: 'col_a_transfers_to_authorized',
		label: 'Transfers to Authorized',
		from: 'col_a_total_receipts',
		group: 'disburse',
		line_number: '18',
		schedule: 'B'
	},
	{
		id: 'col_a_candidate_loan_repayments',
		label: 'to Candidate',
		from: 'col_a_total_loan_repayments',
		group: 'disburse',
		line_number: '19A',
		schedule: 'B'
	},
	{
		id: 'col_a_other_loan_repayments',
		label: 'Other',
		from: 'col_a_total_loan_repayments',
		group: 'disburse',
		line_number: '19B',
		schedule: 'B'
	},
	{
		id: 'col_a_total_loan_repayments',
		label: 'Loan Repayments',
		from: 'col_a_total_receipts',
		group: 'disburse',
		line_number: '19C',
		schedule: 'B'
	},
	{
		id: 'col_a_refunds_to_individuals',
		label: 'to Individuals',
		from: 'col_a_total_refunds',
		group: 'disburse',
		line_number: '20A',
		schedule: 'B'
	},
	{
		id: 'col_a_refunds_to_party_committees',
		label: 'to Party Committees',
		from: 'col_a_total_refunds',
		group: 'disburse',
		line_number: '20B',
		schedule: 'B'
	},
	{
		id: 'col_a_refunds_to_other_committees',
		label: 'to other Committees',
		from: 'col_a_total_refunds',
		group: 'disburse',
		line_number: '20C',
		schedule: 'B'
	},
	{
		id: 'col_a_total_refunds',
		label: 'Refunds',
		from: 'col_a_total_receipts',
		group: 'disburse',
		line_number: '20D',
		schedule: 'B'
	},
	{
		id: 'col_a_other_disbursements',
		label: 'Other Disbursements',
		from: 'col_a_total_receipts',
		group: 'disburse',
		line_number: '21',
		schedule: 'B'
	},
  {
    id: 'col_a_cash_beginning_reporting_period',
    label: 'Cash on Hand',
    to: 'col_a_total_receipts',
    group: 'coh',
    line_number: null,
    schedule: null,
    value: (data: InputRow[]) => {
      const idx = d3.minIndex(data, d => d.coverage_from_date);
      const row = idx >= 0 ? data[idx] : undefined;
      return row?.col_a_cash_beginning_reporting_period ?? 0;
    }
  },
  {
    id: 'col_a_cash_on_hand_close_of_period',
    label: 'Cash on Hand End',
    from: 'col_a_total_receipts',
    group: 'coh',
    line_number: null,
    schedule: null,
    value: (data: InputRow[]) => {
      const idx = d3.maxIndex(data, d => d.coverage_through_date);
      const row = idx >= 0 ? data[idx] : undefined;
      return row?.col_a_cash_on_hand_close_of_period ?? 0;
    }
  }
];

export function F3Sankey(data: InputRow[], params: {width: number, onClick?: (d: F3Node) => void, showCoh: boolean}): SVGSVGElement {
  const { width, onClick, showCoh } = params;
	const links = f3_nodes
  .filter(showCoh ? () => true : (n) => n.group !== 'coh')
		.flatMap((n) =>
			n.from || n.to
				? [
						{
							id: n.id,
							source: n.from ? n.from : n.id,
							target: n.to ? n.to : n.id,
							label: n.label,
							value: n.value ? n.value(data) : d3.sum(data, (d) => d[n.id] as number)
						}
					]
				: []
		)
		.filter((d) => d.value > 0);

	const nodes = f3_nodes
		.map((d) => ({ id: d.id, label: d.label }))
		.filter((d) => links.some((l) => l.source === d.id || l.target === d.id));

	const $ = d3.format('$.3s');

	return SankeyChart(
		{ nodes, links },
		{
			width,
			height: width  * 3 / 4,
			nodeGroup: (d) => f3_nodes.find((d2) => d.id === d2.id)?.group,
			nodeGroups: Object.keys(groupColors),
			colors: Object.values(groupColors),
			nodeAlign: 'justify',
			linkColor: 'source-target',
      nodeWidth: 10,
			nodeLabel: (d) => {
        const {label} = f3_nodes.find((d2) => d.id === d2.id)!;
        return [$(d.value), label];
      },
			nodeTitle: (d) => {
        const {schedule, line_number} = f3_nodes.find((d2) => d.id === d2.id)!;
        return `${schedule}${line_number}`
      },
			format: (d) => $(d),
			onClick: onClick ? (d) => onClick(f3_nodes.find((d2) => d.id === d2.id)!) : undefined
		}
	);
}
