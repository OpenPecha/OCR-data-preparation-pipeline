from pydantic import BaseModel, RootModel
from enum import Enum

class Orientation(str, Enum):
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"

class OCRData(BaseModel):
    name: str
    url: str
    orientation: Orientation
    transcript: str

class OCRDataList(RootModel[list[OCRData]]):
    pass