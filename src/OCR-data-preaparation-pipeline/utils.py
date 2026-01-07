from json import load, dump
from pathlib import Path

def read_json(file_path: Path) -> dict:
    with open(file_path, 'r') as file:
        return load(file)

def save_json(data: dict, file_path: Path):
    with open(file_path, 'w', encoding="utf-8") as file:
        dump(data, file, indent=2, ensure_ascii=False)

def save_failed_ids(failed_ids: list[str], file_path: Path):
    with open(file_path, 'w') as file:
        for fid in failed_ids:
            file.write(f"{fid}\n")