# modules/search.py
import os
from rapidfuzz import fuzz
from model.File import File
from model.Score import Score
from typing import List

def index_files(source_dir: str, excluded_dirs: list[str]) -> List[File]:
    indexed_files: List[File] = []
    
    excluded = [x.strip() for x in excluded_dirs if x.strip()]
    
    for root, dirs, files in os.walk(source_dir):
        dirs[:] = [d for d in dirs if not any(excl in d for excl in excluded)]
        
        for d in dirs:
            if any(excl in d for excl in excluded):
                continue
            dir_path: str = os.path.join(root, d)
            indexed_files.append(File(path=dir_path, content=None, score=Score(0, 0, 0), is_dir=True))
        
        for file in files:
            if any(excl in file for excl in excluded):
                continue
                
            file_path: str = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content: str = f.read()
                indexed_files.append(File(path=file_path, content=content, score=Score(0, 0, 0)))
            except Exception as e:
                print(f"Failed to read {file_path}: {e}")
    return indexed_files

def search_files(query: str, files: List[File], min_score: int = 20) -> List[File]:
    results = []
    query = query.lower()

    for file in files:
        file_name = os.path.basename(file.path).lower()
        full_path = file.path.lower()
        content = file.content.lower() if file.content else ''

        name_score = fuzz.partial_ratio(query, file_name)
        path_score = fuzz.partial_ratio(query, full_path)
        content_score = fuzz.partial_ratio(query, content) if content else 0

        file.score = Score(name=name_score, path=path_score, content=content_score)
        file.score.weight_and_calculate()

        if file.score.total >= min_score:
            results.append(file)

    return sorted(results, key=lambda x: x.score.total, reverse=True)