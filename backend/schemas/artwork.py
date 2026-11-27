from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from pipeline.categories import ImageType, Subject, ArtTechnique
from schemas.tags import TagResponse


class ColorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    r: int
    g: int
    b: int
    l_value: float
    a_value: float
    b_value: float
    percentage: float


class ArtworkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_type: str
    file_path: str
    image_type: Optional[ImageType] = None
    subject: Optional[Subject] = None
    file_extension: str
    art_technique: Optional[ArtTechnique] = None
    tags: list[TagResponse] = []
    reviewed: bool
    colors: list[ColorResponse] = []
    file_url: str = ""

    @field_validator("tags", mode="before")
    @classmethod
    def extract_tag_names(cls, value):
        # `value` here is the list of ArtWorkTag objects that come from the relationship
        return [item.tag for item in value]

    @model_validator(mode="after")
    def build_file_url(self):
        folder = "videos" if self.file_type == "video" else "images"
        self.file_url = f"/{folder}/{self.id}.{self.file_extension}"
        return self


class ArtworkUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    image_type: Optional[ImageType] = None
    subject: Optional[Subject] = None
    art_technique: Optional[ArtTechnique] = None
    tag_ids: Optional[list[int]] = None
    reviewed: Optional[bool] = None


class ArtworkFilter(BaseModel):
    file_type: Optional[str] = None
    image_type: Optional[str] = None
    file_extension: Optional[str] = None
    subject: Optional[str] = None
    art_technique: Optional[str] = None
    tag_ids: Optional[list[int]] = None
    reviewed: Optional[bool] = None
    colors: Optional[list[str]] = None
    color_threshold: float = 50.00


class ArtworkDeleteRequest(BaseModel):
    artwork_ids: list[str]


class SkippedFile(BaseModel):
    name: str
    reason: str


class ImportSummaryResponse(BaseModel):
    imported: list[str] = []
    duplicates: list[str] = []
    skipped: list[SkippedFile] = []


class KnownIdsRequest(BaseModel):
    ids: list[str]


class IngestColor(BaseModel):
    rgb: list[int]
    lab: list[float]
    percentage: float


class IngestMetadata(BaseModel):
    id: str
    file_type: Literal["image", "video"]
    file_extension: str
    image_type: Optional[ImageType] = None
    subject: Optional[Subject] = None
    art_technique: Optional[ArtTechnique] = None
    colors: list[IngestColor] = []

    @field_validator("file_extension")
    @classmethod
    def plain_extension(cls, value: str) -> str:
        if not value.isalnum():
            raise ValueError("file_extension must be alphanumeric")
        return value.lower()
