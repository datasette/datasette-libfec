from pydantic import BaseModel


class RaceSpec(BaseModel):
    office: str
    state: str
    district: str = ""
    cycle: int


class ContributorCriteria(BaseModel):
    first_name: str = ""
    last_name: str = ""
    city: str = ""
    state: str = ""


class FecFilingAlertConfig(BaseModel):
    committee_ids: list[str] = []
    races: list[RaceSpec] = []
    state_filter: str = ""


class FecContributorAlertConfig(BaseModel):
    contributors: list[ContributorCriteria] = []


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
    database_name: str
    candidate: Candidate | None = None
    committee: Committee | None = None
    filings: list[Filing] = []
    error: str | None = None


class CommitteePageData(BaseModel):
    committee_id: str
    cycle: int
    database_name: str
    committee: Committee | None = None
    candidate: Candidate | None = None
    filings: list[Filing] = []
    alerts_available: bool = False
    error: str | None = None


class ContestPageData(BaseModel):
    state: str
    office: str
    district: str | None = None
    cycle: int
    database_name: str
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
    alerts_available: bool = False


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


class DestinationOption(BaseModel):
    id: str
    label: str
    notifier: str


class WatchlistData(BaseModel):
    id: str
    name: str
    watchlist_type: str
    destination_id: str
    destination_label: str = ""
    enabled: bool = True
    committee_ids: list[str] = []
    races: list[RaceSpec] = []
    contributors: list[ContributorCriteria] = []


class AlertLogData(BaseModel):
    watchlist_name: str | None = None
    filing_id: str
    message_text: str | None = None
    sent_at: str | None = None


class AlertsPageData(BaseModel):
    database_name: str
    alerts_available: bool = False
    destinations: list[DestinationOption] = []
    watchlists: list[WatchlistData] = []
    recent_alerts: list[AlertLogData] = []
    prefill_committee_id: str | None = None
    prefill_template: str | None = None


class CronRunData(BaseModel):
    started_at: str = ""
    status: str = ""
    duration_ms: int | None = None
    error_message: str | None = None


class AlertDetailSubscription(BaseModel):
    notifier: str = ""
    destination_label: str = ""


class AlertDetailLogEntry(BaseModel):
    logged_at: str = ""
    new_ids: list[str] = []


class AlertDetailPageData(BaseModel):
    database_name: str
    alert_id: str
    alert_type: str = ""
    type_label: str = ""
    slug: str = ""
    created_at: str | None = None
    frequency: str = ""
    last_check_at: str | None = None
    custom_config: dict = {}
    criteria: list[str] = []
    subscriptions: list[AlertDetailSubscription] = []
    logs: list[AlertDetailLogEntry] = []
    cron_runs: list[CronRunData] = []
    total_runs: int = 0
    success_runs: int = 0
    error_runs: int = 0
    queue_pending: int = 0
    queue_done: int = 0


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
    AlertsPageData,
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
