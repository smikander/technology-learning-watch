import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
HISTORY_FILE = DATA_DIR / "processed_articles.json"


def load_history():
    if not HISTORY_FILE.exists():
        return set()

    with HISTORY_FILE.open(encoding="utf-8") as file:
        history = json.load(file)

    if not isinstance(history, list):
        raise ValueError("Virheellinen historiatiedosto")

    if not all(
        isinstance(url, str) and url.strip()
        for url in history
    ):
        raise ValueError("Virheellinen artikkelin tunniste")

    return set(history)


def save_history(history):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    temporary_file = HISTORY_FILE.with_suffix(".tmp")

    temporary_file.write_text(
        json.dumps(
            sorted(history),
            ensure_ascii=False,
            indent=4
        ),
        encoding="utf-8"
    )

    temporary_file.replace(HISTORY_FILE)
