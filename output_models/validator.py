from pydantic import BaseModel, Field


class AccountValidationOutput(BaseModel):
    validity_check_failed: bool = Field(
        ..., description="Whether any material report verification check failed"
    )
    failure_reasons: list[str] = Field(
        ...,
        description="Distinct reasons the report failed verification; empty if valid",
    )
