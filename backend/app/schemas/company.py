from pydantic import BaseModel


class CompanyOut(BaseModel):
    id: int
    ticker: str
    company_name: str
    sector: str | None
    sector_code: str | None
    description: str | None
    is_active: bool = True

    model_config = {"from_attributes": True}


class CompanyCreate(BaseModel):
    ticker: str
    company_name: str
    sector: str | None = None
    sector_code: str | None = None
    description: str | None = None
    is_active: bool = True
