import re
import unicodedata

def normalize_username(name: str) -> str:
    name = name.lower().strip()
    name = name.replace("đ", "d")
    name = unicodedata.normalize("NFD", name)
    name = name.encode("ascii", "ignore").decode("utf-8")
    name = re.sub(r'[^a-z0-9]', '', name)
    return name

def is_specific_user(name: str) -> bool:
    return normalize_username(name) == "vohuudien"

def is_valid_username(name: str) -> bool:
    return bool(re.fullmatch(r'[A-Za-z0-9_]+', name))
