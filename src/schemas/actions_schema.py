import humps
from pydantic import BaseModel


class CamelCaseSchema(BaseModel):
    class Config:
        alias_generator = humps.camelize
        populate_by_name = True


class CutSchema(CamelCaseSchema):
    cut_from: int
    cut_to: int
    times: int = 1


class VideoEditing(CamelCaseSchema):
    frames: list[CutSchema]
