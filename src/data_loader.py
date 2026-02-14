"""Load themes and question cards from CSV. Paths are fixed; no user input."""

import csv
from pathlib import Path
from typing import TypedDict

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
THEMES_CSV = DATA_DIR / "themes.csv"
QUESTIONS_CSV = DATA_DIR / "questions.csv"

_QUESTIONS_CACHE: dict[str, list[str]] = {}


class Theme(TypedDict):
    """One theme row from themes.csv."""

    id: str
    label: str
    description: str


def get_themes() -> list[Theme]:
    """Return list of theme dicts: id, label, description."""
    themes: list[Theme] = []
    with open(THEMES_CSV, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("id") and row.get("label"):
                themes.append(
                    Theme(
                        id=str(row["id"]).strip(),
                        label=str(row["label"]).strip(),
                        description=str(row.get("description", "")).strip(),
                    )
                )
    return themes


def get_questions(theme_id: str) -> list[str]:
    """Return list of questions for a theme. theme_id must be from get_themes()."""
    if theme_id in _QUESTIONS_CACHE:
        return _QUESTIONS_CACHE[theme_id]
    allowed: set[str] = {t["id"] for t in get_themes()}
    if theme_id not in allowed:
        return []
    out: list[str] = []
    with open(QUESTIONS_CSV, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            tid = row.get("theme_id", "").strip()
            q = row.get("question", "").strip()
            if tid == theme_id and q:
                out.append(q)
    _QUESTIONS_CACHE[theme_id] = out
    return out


def get_all_questions() -> list[tuple[str, str]]:
    """Return list of (theme_id, question) tuples for all questions.

    Used for random mix mode to show which theme each question is from.
    """
    all_questions: list[tuple[str, str]] = []
    themes = get_themes()
    theme_ids = {t["id"] for t in themes}

    with open(QUESTIONS_CSV, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            theme_id = row.get("theme_id", "").strip()
            question = row.get("question", "").strip()
            if theme_id in theme_ids and question:
                all_questions.append((theme_id, question))

    return all_questions
