from pydantic import BaseModel, Field


class InviteLinkCounter(BaseModel):
    count: int = Field(gt=0)