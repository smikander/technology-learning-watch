import sys
import requests

from feed_reader import fetch_articles
from ai_analyzer import analyze_article
from report_generator import generate_report
from history_manager import load_history, save_history


def main():
    print("Technology & Learning Watch")
    print("=" * 50)

    try:
        history = load_history()

    except (OSError, ValueError) as error:
        print(f"Historian lukeminen epäonnistui: {error}")
        return 1

    try:
        articles, failed_sources = fetch_articles()

    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Artikkelien hakeminen epäonnistui: {error}")
        return 1

    new_articles = []
    seen_urls = set(history)

    for article in articles:
        if article["url"] not in seen_urls:
            new_articles.append(article)
            seen_urls.add(article["url"])

    print(f"\nHaettuja artikkeleita: {len(articles)}")
    print(f"Ohitettuja artikkeleita: {len(articles) - len(new_articles)}")
    print(f"Uusia artikkeleita: {len(new_articles)}")
    print(f"Epäonnistuneita lähteitä: {len(failed_sources)}")

    if failed_sources:
        print("Epäonnistuneet lähteet:")

        for source in failed_sources:
            print(f"- {source}")

    if not new_articles:
        print("Ei uusia analysoitavia artikkeleita.")
        return 1 if failed_sources else 0

    analyzed_articles = []

    for index, article in enumerate(new_articles, start=1):
        print(f"\n[{index}/{len(new_articles)}]")
        print(f"Analysoidaan: {article['title']}")

        try:
            analysis = analyze_article(
                article["title"],
                article["description"]
            )

            if not isinstance(analysis, str) or not analysis.strip():
                raise ValueError("Tyhjä tai virheellinen analyysi")

            analyzed_articles.append({
                **article,
                "analysis": analysis
            })

            print("Analyysi valmis.")

        except (
            requests.RequestException,
            KeyError,
            IndexError,
            ValueError,
            TypeError
        ) as error:
            print(f"Analyysi epäonnistui: {error}")

    print("\n" + "=" * 50)
    print(f"Analysoituja artikkeleita: {len(analyzed_articles)}")

    failed_analyses = len(new_articles) - len(analyzed_articles)

    print(f"Epäonnistuneita analyysejä: {failed_analyses}")

    if not analyzed_articles:
        print("Raporttia ei muodostettu.")
        return 1

    try:
        report_path = generate_report(analyzed_articles)
        print(f"\nRaportti tallennettu: {report_path}")

    except OSError as error:
        print(f"Raportin tallennus epäonnistui: {error}")
        return 1

    history.update(
        article["url"] for article in analyzed_articles
    )

    try:
        save_history(history)
        print("Artikkelihistoria päivitetty.")

    except OSError as error:
        print(f"Historian tallennus epäonnistui: {error}")
        return 1

    if failed_sources or failed_analyses:
        print("Suoritus valmistui osittain.")
        return 1

    print("Suoritus onnistui.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
    