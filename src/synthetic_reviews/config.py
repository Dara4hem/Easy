from pathlib import Path
from typing import Dict, List

import yaml
from pydantic import BaseModel


class Persona(BaseModel):
    id: str
    role: str
    tone: str
    rating_range: List[int]


class Config(BaseModel):
    domain: str
    products: List[str]
    personas: List[Persona]
    rating_distribution: Dict[int, float]


def load_config(path: Path) -> Config:
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return Config(**raw)
