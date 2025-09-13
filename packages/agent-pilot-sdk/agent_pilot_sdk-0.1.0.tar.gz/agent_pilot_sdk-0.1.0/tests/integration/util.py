import re


def has_variables(prompt: str) -> bool:
    pattern = r"\{\{.*?\}\}"
    return bool(re.search(pattern, prompt))
