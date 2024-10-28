import os
from rapidfuzz import fuzz

def index_files(source_dir: str, excluded_dirs: list[str]) -> list[tuple[str, str]]:
    indexed_files: list[tuple[str, str]] = []
    for root, dirs, files in os.walk(source_dir):
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        for file in files:
            file_path: str = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content: str = f.read()
                indexed_files.append((file_path, content))
            except Exception as e:
                print(f"Failed to read {file_path}: {e}")
    return indexed_files

def search_files(indexed_files: list[tuple[str, str]], query: str, threshold: int = 60) -> list[tuple[str, str, int]]:
    results: list[tuple[str, str, int]] = []
    for file_path, content in indexed_files:
        file_name = os.path.basename(file_path)
        name_score = fuzz.partial_ratio(query.lower(), file_name.lower())
        content_score = fuzz.partial_ratio(query.lower(), content.lower())
        score = max(name_score, content_score)
        if score >= threshold:
            results.append((file_path, content, score))
    results.sort(key=lambda x: x[2], reverse=True)
    return results
