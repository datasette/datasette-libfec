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


__exports__ = [CandidatePageData, CommitteePageData, ContestPageData, FilingDetailPageData, IndexPageData]