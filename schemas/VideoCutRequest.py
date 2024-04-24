from pydantic import BaseModel


class VideoCutRequest(BaseModel):
    cut_from: int
    cut_to: int
