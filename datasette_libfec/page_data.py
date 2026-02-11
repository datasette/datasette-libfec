from pydantic import BaseModel


class Candidate(BaseModel):
    candidate_id: str
    name: str | None = None
    party_affiliation: str | None = None
    state: str | None = None
    office: str | None = None
    district: str | None = None
    incumbent_challenger_status: str | None = None
    principal_campaign_committee: str | None = None
    address_street1: str | None = None
    address_street2: str | None = None
    address_city: str | None = None
    address_state: str | None = None
    address_zip: str | None = None
    cycle: int | None = None
    # F3 filing data (most recent)
    f3_coverage_through_date: str | None = None
    f3_total_receipts: float | None = None
    f3_total_disbursements: float | None = None
    f3_cash_on_hand_end: float | None = None


class Committee(BaseModel):
    committee_id: str
    name: str | None = None
    committee_type: str | None = None
    designation: str | None = None
    candidate_id: str | None = None
    party_affiliation: str | None = None
    filing_frequency: str | None = None
    address_street1: str | None = None
    address_street2: str | None = None
    address_city: str | None = None
    address_state: str | None = None
    address_zip: str | None = None
    treasurer_name: str | None = None
    cycle: int | None = None


class Filing(BaseModel):
    filing_id: str
    cover_record_form: str | None = None
    filer_id: str | None = None
    filer_name: str | None = None
    coverage_from_date: str | None = None
    coverage_through_date: str | None = None


class CandidatePageData(BaseModel):
    candidate_id: str
    cycle: int
    candidate: Candidate | None = None
    committee: Committee | None = None
    filings: list[Filing] = []
    error: str | None = None


class CommitteePageData(BaseModel):
    committee_id: str
    cycle: int
    committee: Committee | None = None
    candidate: Candidate | None = None
    filings: list[Filing] = []
    error: str | None = None


class ContestPageData(BaseModel):
    state: str
    office: str
    district: str | None = None
    cycle: int
    contest_description: str
    candidates: list[Candidate] = []
    error: str | None = None


class FilingDetailPageData(BaseModel):
    filing_id: str
    filing: Filing | None = None
    form_data: dict | None = None
    database_name: str
    error: str | None = None


class IndexPageData(BaseModel):
    database_name: str
    can_write: bool = False


class ImportPageData(BaseModel):
    database_name: str


class RssPageData(BaseModel):
    database_name: str


class ExportFilingInfo(BaseModel):
    filing_id: str
    success: bool
    message: str | None = None
    # From libfec_filings table
    cover_record_form: str | None = None
    filer_id: str | None = None
    filer_name: str | None = None
    coverage_from_date: str | None = None
    coverage_through_date: str | None = None


class ExportInputInfo(BaseModel):
    id: int
    input_type: str
    input_value: str
    cycle: int | None = None
    filing_ids: list[str] = []


class ExportPageData(BaseModel):
    export_id: int
    export_uuid: str | None = None
    created_at: str | None = None
    status: str | None = None
    filings_count: int = 0
    cover_only: bool = False
    error_message: str | None = None
    inputs: list[ExportInputInfo] = []
    filings: list[ExportFilingInfo] = []
    database_name: str
    error: str | None = None


class FilingDayPageData(BaseModel):
    database_name: str
    years: list[int] = [
        2030,
        2029,
        2028,
        2027,
        2026,
        2025,
        2024,
        2023,
        2022,
        2021,
        2020,
    ]


__exports__ = [
    CandidatePageData,
    CommitteePageData,
    ContestPageData,
    FilingDetailPageData,
    IndexPageData,
    ImportPageData,
    RssPageData,
    ExportPageData,
    FilingDayPageData,
]
