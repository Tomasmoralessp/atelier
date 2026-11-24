from pydantic import BaseModel, ConfigDict, field_validator


class TagCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip().lower()


class TagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
