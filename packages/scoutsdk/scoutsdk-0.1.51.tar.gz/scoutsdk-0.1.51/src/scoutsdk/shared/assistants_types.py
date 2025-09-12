from pydantic import BaseModel


class AssistantFile(BaseModel):
    id: str = ""
    filename: str = ""
    description: str = ""
    status: str = ""
    content_type: str = ""


class AssistantFileUploadResponse(BaseModel):
    message: str
    file_id: str
    assistant_id: str


class AssistantUploadImageResponse(BaseModel):
    content_type: str
    protected_url: str
