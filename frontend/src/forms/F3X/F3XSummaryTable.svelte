<script lang="ts">
  interface Props {
    formData: any;
  }

  let { formData }: Props = $props();

  function usd(value: number | null | undefined): string {
    if (value == null) return '$0';
    return '$' + value.toLocaleString();
  }
</script>

<div class="table-container">
  <table class="summary-table">
    <thead>
      <tr>
        <th></th>
        <th class="col-header">Column A<br /><span class="col-subheader">This Period</span></th>
        <th class="col-header"
          >Column B<br /><span class="col-subheader">Calendar Year-To-Date</span></th
        >
      </tr>
    </thead>
    <tbody>
      <!-- I. Receipts -->
      <tr class="section-header">
        <td colspan="3">I. Receipts</td>
      </tr>
      <tr>
        <td>11. Contributions (other than loans) From:</td>
        <td class="amount"></td>
        <td class="amount"></td>
      </tr>
      <tr>
        <td class="indent">(a) Individuals/Persons Other than Political Committees</td>
        <td class="amount"></td>
        <td class="amount"></td>
      </tr>
      <tr>
        <td class="indent2">(i) Itemized</td>
        <td class="amount">{usd(formData.col_a_individuals_itemized)}</td>
        <td class="amount">{usd(formData.col_b_individuals_itemized)}</td>
      </tr>
      <tr>
        <td class="indent2">(ii) Unitemized</td>
        <td class="amount">{usd(formData.col_a_individuals_unitemized)}</td>
        <td class="amount">{usd(formData.col_b_individuals_unitemized)}</td>
      </tr>
      <tr>
        <td class="indent2">(iii) Total (11(a)(i) + 11(a)(ii))</td>
        <td class="amount">{usd(formData.col_a_individual_contribution_total)}</td>
        <td class="amount">{usd(formData.col_b_individual_contribution_total)}</td>
      </tr>
      <tr>
        <td class="indent">(b) Political Party Committees</td>
        <td class="amount">{usd(formData.col_a_political_party_committees)}</td>
        <td class="amount">{usd(formData.col_b_political_party_committees)}</td>
      </tr>
      <tr>
        <td class="indent">(c) Other Political Committees (such as PACs)</td>
        <td class="amount">{usd(formData.col_a_other_political_committees_pacs)}</td>
        <td class="amount">{usd(formData.col_b_other_political_committees_pacs)}</td>
      </tr>
      <tr>
        <td class="indent">(d) Total Contributions (11(a)(iii) + (b) + (c))</td>
        <td class="amount">{usd(formData.col_a_total_contributions)}</td>
        <td class="amount">{usd(formData.col_b_total_contributions)}</td>
      </tr>
      <tr>
        <td>12. Transfers From Affiliated/Other Party Committees</td>
        <td class="amount">{usd(formData.col_a_transfers_from_aff_other_party_cmttees)}</td>
        <td class="amount">{usd(formData.col_b_transfers_from_aff_other_party_cmttees)}</td>
      </tr>
      <tr>
        <td>13. All Loans Received</td>
        <td class="amount">{usd(formData.col_a_total_loans)}</td>
        <td class="amount">{usd(formData.col_b_total_loans)}</td>
      </tr>
      <tr>
        <td>14. Loan Repayments Received</td>
        <td class="amount">{usd(formData.col_a_total_loan_repayments_received)}</td>
        <td class="amount">{usd(formData.col_b_total_loan_repayments_received)}</td>
      </tr>
      <tr>
        <td>15. Offsets to Operating Expenditures (Refunds, Rebates, etc)</td>
        <td class="amount">{usd(formData.col_a_offsets_to_expenditures)}</td>
        <td class="amount">{usd(formData.col_b_offsets_to_expenditures)}</td>
      </tr>
      <tr>
        <td>16. Refunds of Contributions made to Fed. Candidates and other Political Committees</td>
        <td class="amount">{usd(formData.col_a_federal_refunds)}</td>
        <td class="amount">{usd(formData.col_b_federal_refunds)}</td>
      </tr>
      <tr>
        <td>17. Other Federal Receipts (Dividends, Interest, etc)</td>
        <td class="amount">{usd(formData.col_a_other_federal_receipts)}</td>
        <td class="amount">{usd(formData.col_b_other_federal_receipts)}</td>
      </tr>
      <tr>
        <td>18. Transfers from Non-Federal and Levin Funds</td>
        <td class="amount"></td>
        <td class="amount"></td>
      </tr>
      <tr>
        <td class="indent">(a) Non-Federal Account (SCHEDULE H3)</td>
        <td class="amount">{usd(formData.col_a_transfers_from_nonfederal_h3)}</td>
        <td class="amount">{usd(formData.col_b_transfers_from_nonfederal_h3)}</td>
      </tr>
      <tr>
        <td class="indent">(b) Levin Funds (SCHEDULE H5)</td>
        <td class="amount">{usd(formData.col_a_levin_funds)}</td>
        <td class="amount">{usd(formData.col_b_levin_funds)}</td>
      </tr>
      <tr>
        <td class="indent">(c) Total Transfers ( 18(a) + 18(b) )</td>
        <td class="amount">{usd(formData.col_a_total_nonfederal_transfers)}</td>
        <td class="amount">{usd(formData.col_b_total_nonfederal_transfers)}</td>
      </tr>
      <tr class="subtotal">
        <td>19. Total Receipts (11(d) + 12 + 13 + 14 + 15 + 16 + 17 + 18)</td>
        <td class="amount">{usd(formData.col_a_total_receipts)}</td>
        <td class="amount">{usd(formData.col_b_total_receipts)}</td>
      </tr>
      <tr>
        <td>20. Total Federal Receipts (19 - 18(c))</td>
        <td class="amount">{usd(formData.col_a_total_federal_receipts)}</td>
        <td class="amount">{usd(formData.col_b_total_federal_receipts)}</td>
      </tr>

      <!-- II. Disbursements -->
      <tr class="section-header">
        <td colspan="3">II. Disbursements</td>
      </tr>
      <tr>
        <td>21. Operating Expenditures</td>
        <td class="amount"></td>
        <td class="amount"></td>
      </tr>
      <tr>
        <td class="indent">(a) Shared Federal/Nonfederal Activity (SCHEDULE H4)</td>
        <td class="amount"></td>
        <td class="amount"></td>
      </tr>
      <tr>
        <td class="indent2">(i) Federal Share</td>
        <td class="amount">{usd(formData.col_a_shared_operating_expenditures_federal)}</td>
        <td class="amount">{usd(formData.col_b_shared_operating_expenditures_federal)}</td>
      </tr>
      <tr>
        <td class="indent2">(ii) Nonfederal Share</td>
        <td class="amount">{usd(formData.col_a_shared_operating_expenditures_nonfederal)}</td>
        <td class="amount">{usd(formData.col_b_shared_operating_expenditures_nonfederal)}</td>
      </tr>
      <tr>
        <td class="indent">(b) Other Federal Operating Expenditures</td>
        <td class="amount">{usd(formData.col_a_other_federal_operating_expenditures)}</td>
        <td class="amount">{usd(formData.col_b_other_federal_operating_expenditures)}</td>
      </tr>
      <tr>
        <td class="indent">(c) Total Operating Expenditures (21(a)(i) + (a)(ii) + (b))</td>
        <td class="amount">{usd(formData.col_a_total_operating_expenditures)}</td>
        <td class="amount">{usd(formData.col_b_total_operating_expenditures)}</td>
      </tr>
      <tr>
        <td>22. Transfers to Affiliated/Other Party Committees</td>
        <td class="amount">{usd(formData.col_a_transfers_to_affiliated)}</td>
        <td class="amount">{usd(formData.col_b_transfers_to_affiliated)}</td>
      </tr>
      <tr>
        <td>23. Contributions to Fed. Candidates/Committees and Other Political Committees</td>
        <td class="amount">{usd(formData.col_a_contributions_to_candidates)}</td>
        <td class="amount">{usd(formData.col_b_contributions_to_candidates)}</td>
      </tr>
      <tr>
        <td>24. Independent Expenditures (SCHEDULE E)</td>
        <td class="amount">{usd(formData.col_a_independent_expenditures)}</td>
        <td class="amount">{usd(formData.col_b_independent_expenditures)}</td>
      </tr>
      <tr>
        <td>25. Coordinated Expenditures Made by Party Committees (SCHEDULE F)</td>
        <td class="amount">{usd(formData.col_a_coordinated_expenditures_by_party_committees)}</td>
        <td class="amount">{usd(formData.col_b_coordinated_expenditures_by_party_committees)}</td>
      </tr>
      <tr>
        <td>26. Loan Repayments Made</td>
        <td class="amount">{usd(formData.col_a_total_loan_repayments_made)}</td>
        <td class="amount">{usd(formData.col_b_total_loan_repayments_made)}</td>
      </tr>
      <tr>
        <td>27. Loans Made</td>
        <td class="amount">{usd(formData.col_a_loans_made)}</td>
        <td class="amount">{usd(formData.col_b_loans_made)}</td>
      </tr>
      <tr>
        <td>28. Refunds of Contributions To:</td>
        <td class="amount"></td>
        <td class="amount"></td>
      </tr>
      <tr>
        <td class="indent">(a) Individuals/Persons Other Than Political Committees</td>
        <td class="amount">{usd(formData.col_a_refunds_to_individuals)}</td>
        <td class="amount">{usd(formData.col_b_refunds_to_individuals)}</td>
      </tr>
      <tr>
        <td class="indent">(b) Political Party Committees</td>
        <td class="amount">{usd(formData.col_a_refunds_to_party_committees)}</td>
        <td class="amount">{usd(formData.col_b_refunds_to_party_committees)}</td>
      </tr>
      <tr>
        <td class="indent">(c) Other Political Committees (such as PACs)</td>
        <td class="amount">{usd(formData.col_a_refunds_to_other_committees)}</td>
        <td class="amount">{usd(formData.col_b_refunds_to_other_committees)}</td>
      </tr>
      <tr>
        <td class="indent">(d) Total Contribution Refunds (28(a) + (b) + (c))</td>
        <td class="amount">{usd(formData.col_a_total_refunds)}</td>
        <td class="amount">{usd(formData.col_b_total_refunds)}</td>
      </tr>
      <tr>
        <td>29. Other Disbursements</td>
        <td class="amount">{usd(formData.col_a_other_disbursements)}</td>
        <td class="amount">{usd(formData.col_b_other_disbursements)}</td>
      </tr>
      <tr>
        <td>30. Federal Election Activity</td>
        <td class="amount"></td>
        <td class="amount"></td>
      </tr>
      <tr>
        <td class="indent"
          >(a) (i) Allocated Federal Election Activity - Federal Share (SCHEDULE H6)</td
        >
        <td class="amount">{usd(formData.col_a_federal_election_activity_federal_share)}</td>
        <td class="amount">{usd(formData.col_b_federal_election_activity_federal_share)}</td>
      </tr>
      <tr>
        <td class="indent"
          >(a) (ii) Allocated Federal Election Activity - Levin Share (SCHEDULE H6)</td
        >
        <td class="amount">{usd(formData.col_a_federal_election_activity_levin_share)}</td>
        <td class="amount">{usd(formData.col_b_federal_election_activity_levin_share)}</td>
      </tr>
      <tr>
        <td class="indent">(b) Federal Election Activity Paid Entirely with Federal Funds</td>
        <td class="amount">{usd(formData.col_a_federal_election_activity_all_federal)}</td>
        <td class="amount">{usd(formData.col_b_federal_election_activity_all_federal)}</td>
      </tr>
      <tr>
        <td class="indent">(c) Total Federal Election Activity ( 30(a)(i)+30(a)(ii)+30(b) )</td>
        <td class="amount">{usd(formData.col_a_federal_election_activity_total)}</td>
        <td class="amount">{usd(formData.col_b_federal_election_activity_total)}</td>
      </tr>
      <tr class="subtotal">
        <td>31. Total Disbursements ( 21(c)+23+24+25+26+27+28(d)+29+30(c) )</td>
        <td class="amount">{usd(formData.col_a_total_disbursements)}</td>
        <td class="amount">{usd(formData.col_b_total_disbursements)}</td>
      </tr>
      <tr>
        <td>32. Total Federal Disbursements (31-21(a)(ii)-30(a)(ii))</td>
        <td class="amount">{usd(formData.col_a_total_federal_disbursements)}</td>
        <td class="amount">{usd(formData.col_b_total_federal_disbursements)}</td>
      </tr>

      <!-- III. Net Contributions/Operating Expenditures -->
      <tr class="section-header">
        <td colspan="3">III. Net Contributions/Operating Expenditures</td>
      </tr>
      <tr>
        <td>33. Total Contributions (other than loans) (11(d))</td>
        <td class="amount">{usd(formData.col_a_total_contributions)}</td>
        <td class="amount">{usd(formData.col_b_total_contributions)}</td>
      </tr>
      <tr>
        <td>34. Total Contribution Refunds (28(d))</td>
        <td class="amount">{usd(formData.col_a_total_refunds)}</td>
        <td class="amount">{usd(formData.col_b_total_refunds)}</td>
      </tr>
      <tr>
        <td>35. Net Contributions (other than loans) (33 - 34)</td>
        <td class="amount">{usd(formData.col_a_net_contributions)}</td>
        <td class="amount">{usd(formData.col_b_net_contributions)}</td>
      </tr>
      <tr>
        <td>36. Total Federal Operating Expenditures (21(a)(i) + 21(b))</td>
        <td class="amount">{usd(formData.col_a_total_federal_operating_expenditures)}</td>
        <td class="amount">{usd(formData.col_b_total_federal_operating_expenditures)}</td>
      </tr>
      <tr>
        <td>37. Offsets to Operating Expenditures (15)</td>
        <td class="amount">{usd(formData.col_a_total_offsets_to_expenditures)}</td>
        <td class="amount">{usd(formData.col_b_total_offsets_to_expenditures)}</td>
      </tr>
      <tr>
        <td>38. Net Operating Expenditures</td>
        <td class="amount">{usd(formData.col_a_net_operating_expenditures)}</td>
        <td class="amount">{usd(formData.col_b_net_operating_expenditures)}</td>
      </tr>
    </tbody>
  </table>
</div>

<style>
  .table-container {
    overflow-x: auto;
    display: flex;
    justify-content: center;
  }

  .summary-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 1rem;
    max-width: 720px;
  }

  .summary-table th,
  .summary-table td {
    border: 1px solid #ddd;
    padding: 0.5rem;
  }

  .summary-table th {
    text-align: right;
    background: #f5f5f5;
    font-weight: 600;
  }

  .summary-table th:first-child {
    width: 50%;
  }

  .col-header {
    width: 25%;
    text-align: right;
  }

  .col-subheader {
    font-size: 0.9rem;
    font-weight: normal;
  }

  .section-header td {
    background: #f9f9f9;
    font-weight: 600;
  }

  .indent {
    padding-left: 1.5rem !important;
  }

  .indent2 {
    padding-left: 3rem !important;
  }

  .subtotal td {
    font-weight: 600;
  }

  .amount {
    text-align: right;
  }
</style>
