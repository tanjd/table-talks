"""CSV file data source implementation."""

import csv
from pathlib import Path

from .base import DataSource, Theme


class CSVDataSource(DataSource):
    """Load themes and questions from CSV files."""

    def __init__(self, data_dir: Path | None = None):
        """Initialize CSV data source.

        Args:
            data_dir: Directory containing themes.csv and questions.csv.
                     Defaults to ../data relative to this file.
        """
        if data_dir is None:
            data_dir = Path(__file__).resolve().parent.parent.parent / "data"
        self.data_dir = Path(data_dir)
        self.themes_csv = self.data_dir / "themes.csv"
        self.questions_csv = self.data_dir / "questions.csv"

        # Cache for questions by theme (matches existing behavior)
        self._questions_cache: dict[str, list[str]] = {}

    def get_themes(self) -> list[Theme]:
        """Return list of theme dicts: id, label, description."""
        themes: list[Theme] = []
        with open(self.themes_csv, encoding="utf-8", newline="") as f:
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

    def get_questions(self, theme_id: str) -> list[str]:
        """Return list of questions for a theme. theme_id must be from get_themes()."""
        # Check cache first
        if theme_id in self._questions_cache:
            return self._questions_cache[theme_id]

        # Validate theme exists
        allowed: set[str] = {t["id"] for t in self.get_themes()}
        if theme_id not in allowed:
            return []

        # Load questions for this theme
        out: list[str] = []
        with open(self.questions_csv, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                tid = row.get("theme_id", "").strip()
                q = row.get("question", "").strip()
                if tid == theme_id and q:
                    out.append(q)

        # Cache the result
        self._questions_cache[theme_id] = out
        return out

    def get_all_questions(self) -> list[tuple[str, str]]:
        """Return list of (theme_id, question) tuples for all questions.

        Used for random mix mode to show which theme each question is from.
        """
        all_questions: list[tuple[str, str]] = []
        themes = self.get_themes()
        theme_ids = {t["id"] for t in themes}

        with open(self.questions_csv, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                theme_id = row.get("theme_id", "").strip()
                question = row.get("question", "").strip()
                if theme_id in theme_ids and question:
                    all_questions.append((theme_id, question))

        return all_questions
