
import json
import pytest

import dashboard_data
from dashboard_data import (
    parse_fields,
    normalize_article,
    calculate_statistics,
    list_reports,
    load_report
)


@pytest.fixture
def sample_article():
    return {
        "title": "Python API Testing",
        "source": "Python Insider",
        "category": "Python",
        "published": "2026-11-24",
        "url": "https://example.com/article",
        "analysis": (
            "**Tiivistelmä:** Artikkeli käsittelee testausta.\n"
            "**Hyöty:** Parempi ohjelmiston laatu.\n"
            "**Oppimisehdotus:** Tutustu pytestiin.\n"
            "**Osaamisalue:** Python, Testing, API\n"
            "**Hyödyllisyys:** 4 – Hyödyllinen artikkeli."
        )
    }


@pytest.mark.parametrize("text", [
    "**Tiivistelmä:** Testisisältö",
    "**Tiivistelmä:**\nTestisisältö",
    "Tiivistelmä: Testisisältö",
    "**Tiivistelmä**: Testisisältö"
])
def test_parse_fields_formats(text):
    assert parse_fields(text)["summary"] == "Testisisältö"


def test_parse_multiline_field():
    text = "Tiivistelmä: Ensimmäinen lause.\nToinen lause."

    assert parse_fields(text)["summary"] == (
        "Ensimmäinen lause. Toinen lause."
    )


def test_parse_multiple_fields():
    fields = parse_fields(
        "Tiivistelmä: Testi\n"
        "Hyöty: Laatu\n"
        "Oppimisehdotus: Harjoittele"
    )

    assert fields["summary"] == "Testi"
    assert fields["benefit"] == "Laatu"
    assert fields["learning_suggestion"] == "Harjoittele"


def test_parse_empty_analysis():
    assert parse_fields("") == {}


def test_normalize_article(sample_article):
    article = normalize_article(sample_article)

    assert article["title"] == "Python API Testing"
    assert article["rating"] == 4
    assert article["summary"] == "Artikkeli käsittelee testausta."
    assert article["skills"] == ["Python", "Testing", "API"]
    assert article["url"] == "https://example.com/article"


@pytest.mark.parametrize("value, expected", [
    ("1 – Perustelu", 1),
    ("3/5 – Perustelu", 3),
    ("5 – Perustelu", 5),
    ("0 – Virheellinen", None),
    ("6 – Virheellinen", None),
    ("Ei arviota", None),
    ("", None)
])
def test_article_rating(sample_article, value, expected):
    sample_article["analysis"] = f"Hyödyllisyys: {value}"

    assert normalize_article(sample_article)["rating"] == expected


@pytest.mark.parametrize("url", [
    "javascript:alert(1)",
    "http://example.com",
    "https://user:password@example.com",
    "https://example.com/invalid path",
    "https://",
    "",
    None
])
def test_unsafe_article_urls(sample_article, url):
    sample_article["url"] = url

    assert normalize_article(sample_article)["url"] is None


def test_missing_article_fields():
    article = normalize_article({})

    assert article["title"] == "Nimetön artikkeli"
    assert article["rating"] is None
    assert article["skills"] == []
    assert article["url"] is None


def test_calculate_statistics():
    articles = [
        {"category": "Python", "source": "A", "rating": 4},
        {"category": "Python", "source": "A", "rating": 5},
        {"category": "AI", "source": "B", "rating": None}
    ]

    stats = calculate_statistics(articles)

    assert stats["article_count"] == 3
    assert stats["source_count"] == 2
    assert stats["category_count"] == 2
    assert stats["average_rating"] == 4.5
    assert stats["categories"] == {"Python": 2, "AI": 1}
    assert stats["sources"] == {"A": 2, "B": 1}


def test_empty_statistics():
    stats = calculate_statistics([])

    assert stats["article_count"] == 0
    assert stats["source_count"] == 0
    assert stats["category_count"] == 0
    assert stats["average_rating"] is None
    assert stats["categories"] == {}
    assert stats["sources"] == {}


def test_statistics_without_ratings():
    stats = calculate_statistics([
        {"category": "Python", "source": "A", "rating": None}
    ])

    assert stats["average_rating"] is None


def test_list_reports_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(dashboard_data, "REPORT_DIR", tmp_path)

    assert list_reports() == []


def test_list_reports_order(tmp_path, monkeypatch):
    monkeypatch.setattr(dashboard_data, "REPORT_DIR", tmp_path)

    older = tmp_path / "learning-report-2026-11-24.md"
    newer = tmp_path / "learning-report-2026-11-25.md"

    older.touch()
    newer.touch()

    assert list_reports() == [newer, older]


def test_json_report_preferred(tmp_path, monkeypatch):
    monkeypatch.setattr(dashboard_data, "REPORT_DIR", tmp_path)

    markdown = tmp_path / "learning-report-2026-11-24.md"
    json_report = markdown.with_suffix(".json")

    markdown.touch()
    json_report.touch()

    assert list_reports() == [json_report]


def test_unrelated_files_ignored(tmp_path, monkeypatch):
    monkeypatch.setattr(dashboard_data, "REPORT_DIR", tmp_path)

    (tmp_path / "other.json").touch()
    (tmp_path / "notes.md").touch()

    assert list_reports() == []


def test_load_json_report(tmp_path, sample_article):
    path = tmp_path / "learning-report-test.json"

    path.write_text(
        json.dumps({
            "created_at": "2026-11-24T19:18:00",
            "articles": [sample_article]
        }),
        encoding="utf-8"
    )

    report = load_report(path)

    assert report["statistics"]["article_count"] == 1
    assert report["articles"][0]["rating"] == 4


def test_load_markdown_report(tmp_path):
    path = tmp_path / "learning-report-test.md"

    path.write_text(
        "# Technology & Learning Watch\n"
        "Raportti luotu: 24.11.2026 19:18\n"
        "## 1. Python Testing\n"
        "**Lähde:** Python Insider\n"
        "**Aihealue:** Python\n"
        "**Tiivistelmä:**\n"
        "Artikkeli käsittelee testausta.\n"
        "**Hyödyllisyys:** 4 – Hyödyllinen.\n"
        "**Alkuperäinen artikkeli:** https://example.com\n"
        "---\n"
        "## Huomautus\n"
        "Tekoälyn tuottamaa sisältöä.",
        encoding="utf-8"
    )

    report = load_report(path)

    assert report["created_at"] == "24.11.2026 19:18"
    assert report["statistics"]["article_count"] == 1
    assert report["articles"][0]["title"] == "Python Testing"
    assert report["articles"][0]["rating"] == 4
    assert report["articles"][0]["summary"] == (
        "Artikkeli käsittelee testausta."
    )


def test_invalid_json_report(tmp_path):
    path = tmp_path / "learning-report-invalid.json"
    path.write_text("invalid json", encoding="utf-8")

    with pytest.raises(ValueError):
        load_report(path)
