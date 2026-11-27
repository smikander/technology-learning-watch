import json
from pathlib import Path
import feedparser
import requests
from datetime import datetime, timedelta, timezone
from calendar import timegm
from html.parser import HTMLParser
import re
from urllib.parse import urlsplit

BASE_DIR = Path(__file__).resolve().parent
MAX_FEED_BYTES = 5 * 1024 * 1024


def load_config():
    with open(BASE_DIR / "config.json", encoding="utf-8") as file:
        config = json.load(file)

    if not isinstance(config, dict):
        raise ValueError("Virheellinen asetustiedosto")

    for key in ("max_articles_per_feed", "max_article_age_days"):
        value = config.get(key)

        if type(value) is not int or value <= 0:
            raise ValueError(f"Virheellinen asetus: {key}")

    feeds = config.get("feeds")

    if not isinstance(feeds, list) or not feeds:
        raise ValueError("RSS-lähteitä ei ole määritelty")

    for source in feeds:
        if not isinstance(source, dict):
            raise ValueError("Virheellinen RSS-lähde")

        for key in ("name", "category", "url"):
            value = source.get(key)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Virheellinen lähteen asetus: {key}")

        parsed_url = urlsplit(source["url"])

        if (
            parsed_url.scheme != "https"
            or not parsed_url.hostname
            or parsed_url.username is not None
            or parsed_url.password is not None
        ):
            raise ValueError("RSS-lähteen URL ei ole sallittu")

    return config


def is_recent_article(entry, max_age_days):
    published = (
        entry.get("published_parsed")
        or entry.get("updated_parsed")
    )

    if not published:
        return False

    published_date = datetime.fromtimestamp(
        timegm(published),
        tz=timezone.utc
    )

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=max_age_days)

    return cutoff <= published_date <= now


class DescriptionParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def get_text(self):
        return " ".join(self.parts)
    

def clean_description(description):
    if not isinstance(description, str):
        return ""

    parser = DescriptionParser()
    parser.feed(description)
    parser.close()

    text = parser.get_text()
    text = re.sub(r"\s+", " ", text)

    return text.strip()[:3000]


def fetch_feed(source, limit, max_age_days):
    with requests.get(
        source["url"],
        timeout=(5, 15),
        headers={"User-Agent": "TechnologyLearningWatch/0.1"},
        stream=True,
        allow_redirects=False
    ) as response:

        response.raise_for_status()

        if response.status_code != 200:
            raise ValueError(
                f"Odottamaton HTTP-tilakoodi: {response.status_code}"
            )

        content = bytearray()

        for chunk in response.iter_content(chunk_size=8192):
            if len(content) + len(chunk) > MAX_FEED_BYTES:
                raise ValueError("RSS-syöte ylittää kokorajoituksen")

            content.extend(chunk)

    feed = feedparser.parse(bytes(content))

    if feed.bozo and not feed.entries:
        raise ValueError("Virheellinen RSS-syöte")

    articles = []

    for entry in feed.entries:
        if not is_recent_article(entry, max_age_days):
            continue

        article = {
            "source": source["name"],
            "category": source["category"],
            "title": entry.get("title", "").strip(),
            "description": clean_description(
                entry.get("summary", "")
            ),
            "url": entry.get("link", ""),
            "published": (
                entry.get("published")
                or entry.get("updated", "")
            )
        }

        if (
            article["title"]
            and article["url"]
            and article["description"]
        ):
            articles.append(article)

        if len(articles) >= limit:
            break

    return articles


def fetch_articles():
    config = load_config()
    articles = []
    failed_sources = []

    for source in config["feeds"]:
        try:
            results = fetch_feed(
                source,
                config["max_articles_per_feed"],
                config["max_article_age_days"]
            )

            articles.extend(results)

            print(
                f"{source['name']}: "
                f"{len(results)} artikkelia"
            )

        except (requests.RequestException, ValueError) as error:
            failed_sources.append(source["name"])
            print(f"{source['name']}: Haku epäonnistui: {error}")

    return articles, failed_sources


if __name__ == "__main__":
    articles, failed_sources = fetch_articles()

    print(f"\nArtikkeleita yhteensä: {len(articles)}")
    print(f"Epäonnistuneita lähteitä: {len(failed_sources)}\n")

    for source in failed_sources:
        print(f"Epäonnistunut lähde: {source}")

    for article in articles:
        print(f"Lähde: {article['source']}")
        print(f"Otsikko: {article['title']}")
        print(f"Julkaistu: {article['published']}")
        print(f"Linkki: {article['url']}")
        print("-" * 50)
