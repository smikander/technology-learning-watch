
import json
import re

from collections import Counter
from pathlib import Path
from report_generator import safe_article_url

BASE_DIR = Path(__file__).resolve().parent
REPORT_DIR = BASE_DIR / "reports"

FIELD_MAP = {
    "Lähde": "source",
    "Aihealue": "category",
    "Julkaistu": "published",
    "Tiivistelmä": "summary",
    "Hyöty": "benefit",
    "Oppimisehdotus": "learning_suggestion",
    "Osaamisalue": "skills",
    "Hyödyllisyys": "usefulness",
    "Alkuperäinen artikkeli": "url"
}

FIELD_PATTERN = re.compile(
    r"^\s*(?:\*\*)?("
    + "|".join(re.escape(field) for field in FIELD_MAP)
    + r")(?:\*\*)?:\s*(?:\*\*)?\s*(.*)$"
)


def parse_fields(text):
    fields = {}
    current_field = None

    for line in text.splitlines():
        line = line.strip()

        if line == "---" or line.startswith("## "):
            current_field = None
            continue

        match = FIELD_PATTERN.match(line)

        if match:
            current_field = FIELD_MAP[match.group(1)]
            fields[current_field] = match.group(2).strip()

        elif current_field and line:
            fields[current_field] += " " + line

    return {
        key: value.strip()
        for key, value in fields.items()
    }


def normalize_article(article):
    analysis = article.get("analysis", "")
    fields = parse_fields(analysis)

    usefulness = fields.get(
        "usefulness",
        article.get("usefulness", "")
    )

    rating_match = re.match(
        r"^([1-5])(?:/5)?(?=\s|[–—-]|$)",
        usefulness
    )

    rating = int(rating_match.group(1)) if rating_match else None

    skills = fields.get("skills", article.get("skills", ""))

    url = safe_article_url(article.get("url", ""))

    return {
        "title": article.get("title", "Nimetön artikkeli"),
        "source": article.get("source", "Tuntematon"),
        "category": article.get("category", "Muut"),
        "published": article.get("published", ""),
        "url": url if url.startswith("https://") else None,
        "summary": fields.get("summary", article.get("summary", "")),
        "benefit": fields.get("benefit", article.get("benefit", "")),
        "learning_suggestion": fields.get(
            "learning_suggestion",
            article.get("learning_suggestion", "")
        ),
        "skills": [
            skill.strip().rstrip(".")
            for skill in skills.split(",")
            if skill.strip()
        ],
        "rating": rating,
        "usefulness": usefulness,
        "raw_analysis": analysis
    }


def list_reports():
    reports = {}

    for extension in (".md", ".json"):
        for path in REPORT_DIR.glob(f"learning-report-*{extension}"):
            if path.is_file():
                reports[path.stem] = path

    return sorted(
        reports.values(),
        key=lambda path: path.stem,
        reverse=True
    )


def read_markdown_report(path):
    content = path.read_text(encoding="utf-8")

    date_match = re.search(
        r"^Raportti luotu:\s*(.+)$",
        content,
        re.MULTILINE
    )

    sections = re.split(
        r"^## \d+\.\s+",
        content,
        flags=re.MULTILINE
    )

    articles = []

    for section in sections[1:]:
        section = section.split("\n## Huomautus", 1)[0]

        title, _, body = section.partition("\n")

        fields = parse_fields(body)
        fields["title"] = title.strip()

        articles.append(fields)

    return {
        "created_at": date_match.group(1) if date_match else "",
        "articles": articles
    }


def load_report(path):
    if path.suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = read_markdown_report(path)

    articles = [
        normalize_article(article)
        for article in data["articles"]
    ]

    return {
        "created_at": data.get("created_at", ""),
        "articles": articles,
        "statistics": calculate_statistics(articles)
    }


def calculate_statistics(articles):
    categories = Counter(
        article["category"] for article in articles
    )

    sources = Counter(
        article["source"] for article in articles
    )

    ratings = [
        article["rating"]
        for article in articles
        if article["rating"] is not None
    ]

    return {
        "article_count": len(articles),
        "source_count": len(sources),
        "category_count": len(categories),
        "average_rating": (
            round(sum(ratings) / len(ratings), 1)
            if ratings else None
        ),
        "categories": dict(categories.most_common()),
        "sources": dict(sources.most_common())
    }
