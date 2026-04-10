from pydantic import BaseModel


class UserInfo(BaseModel):
    username: str
    avatar_url: str | None = None


class ValidationMessage(BaseModel):
    level: str  # "error" or "warning"
    message: str


class ValidationResult(BaseModel):
    valid: bool
    errors: list[str]
    warnings: list[str]
    pack_name: str | None = None


class UploadResponse(BaseModel):
    success: bool
    pr_url: str | None = None
    pr_number: int | None = None
    pack_name: str | None = None
    errors: list[str] | None = None
    warnings: list[str] | None = None


class SubmissionInfo(BaseModel):
    pr_number: int
    title: str
    state: str  # open, closed, merged
    ci_status: str | None  # pending, success, failure
    created_at: str
    url: str
    pack_name: str | None = None
