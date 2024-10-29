# model/File.py
from dataclasses import dataclass
from typing import Optional
from .Score import Score

@dataclass
class File:
    path: str
    content: Optional[str]
    score: Score
    is_dir: bool = False