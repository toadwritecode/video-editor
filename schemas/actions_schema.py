from pydantic import BaseModel


class CutSchema(BaseModel):
    cut_from: int
    cut_to: int
