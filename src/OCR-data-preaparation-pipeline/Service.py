from Models import Orientation
from PIL import Image
from pathlib import Path
from typing import List


def get_image_url(name: str) -> str:
    return f"https://s3.us-east-1.amazonaws.com/bec.data/OCR-Benchmark/B1/{name}"

def load_image(image_path: Path) -> Image.Image:
    image = Image.open(image_path)
    image = image.convert("RGB")
    return image

def determine_orientation(label: str) -> Orientation:
    if label == "portrait":
        return Orientation.PORTRAIT
    return Orientation.LANDSCAPE

def ocr_image(name: str) -> str:
    text = Path(f"/Users/tashitsering/Desktop/B1/{name}.txt").read_text(encoding="utf-8", )
    return text 
