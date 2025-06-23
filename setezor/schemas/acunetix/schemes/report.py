from pydantic import BaseModel


class ReportTemplate(BaseModel):
    name: str
    group: str
    template_id: str
    accepted_sources: list[str]


class ReportCreate(BaseModel):
    template_id: str


class ReportAddForm(BaseModel):
    scan_id: str
    template_id: str


class Source(BaseModel):
    list_type: str | None = None
    description: str
    id_list: list[str]


class Report(BaseModel):
    download: list[str]
    generation_date: str
    report_id: str
    source: Source
    status: str
    template_id: str
    template_name: str
    template_type: int