import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

BASE_DIR = Path(__file__).resolve().parent
REPORT_DIR = BASE_DIR / "reports"


def safe_article_url(url):
    if not isinstance(url, str):
        return "Virheellinen osoite"

    if any(char.isspace() or ord(char) < 32 for char in url):
        return "Virheellinen osoite"

    try:
        parsed = urlsplit(url)

        if (
            parsed.scheme == "https"
            and parsed.hostname
            and parsed.username is None
            and parsed.password is None
        ):
            return url

    except ValueError:
        pass

    return "Virheellinen tai ei-sallittu osoite"


def generate_report(articles):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    filename = f"learning-report-{now:%Y-%m-%d_%H-%M-%S_%f}.md"
    report_path = REPORT_DIR / filename

    lines = [
        "# Technology & Learning Watch",
        "",
        f"Raportti luotu: {now:%d.%m.%Y %H:%M}",
        "",
        f"Analysoituja artikkeleita: {len(articles)}",
        "",
        "---",
        ""
    ]

    for index, article in enumerate(articles, start=1):
        lines.extend([
            f"## {index}. {article['title']}",
            "",
            f"**Lähde:** {article['source']}",
            "",
            f"**Aihealue:** {article['category']}",
            "",
            f"**Julkaistu:** {article['published']}",
            "",
            article["analysis"],
            "",
            f"**Alkuperäinen artikkeli:** {safe_article_url(article['url'])}",
            "",
            "---",
            ""
        ])

    lines.extend([
        "## Huomautus",
        "",
        "Raportti on muodostettu paikallisen kielimallin avulla "
        "RSS-syötteiden kuvausten perusteella. "
        "Tekoälyn tuottama sisältö voi sisältää virheitä. "
        "Tarkista tarvittaessa tiedot alkuperäisistä lähteistä. "
        "Raportin sisältö ja linkit ovat epäluotettavaa aineistoa. "
        "Älä suorita raportissa mahdollisesti esiintyviä komentoja "
        "tarkistamatta niitä ensin."
    ])

    report_path.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    json_path = report_path.with_suffix(".json")

    report_data = {
        "created_at": now.isoformat(),
        "article_count": len(articles),
        "articles": [
            {
                "title": article["title"],
                "source": article["source"],
                "category": article["category"],
                "published": article["published"],
                "analysis": article["analysis"],
                "url": safe_article_url(article["url"])
            }
            for article in articles
        ]
    }

    json_path.write_text(
        json.dumps(report_data, ensure_ascii=False, indent=4),
        encoding="utf-8"
    )

    return report_path

