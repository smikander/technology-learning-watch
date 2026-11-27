
"use strict";

const elements = {
    dashboard: document.querySelector("#dashboard"),
    status: document.querySelector("#status-message"),
    reportSelect: document.querySelector("#report-select"),
    reportDate: document.querySelector("#report-date"),
    articleCount: document.querySelector("#article-count"),
    sourceCount: document.querySelector("#source-count"),
    categoryCount: document.querySelector("#category-count"),
    averageRating: document.querySelector("#average-rating"),
    categoryChart: document.querySelector("#category-chart"),
    sourceChart: document.querySelector("#source-chart"),
    search: document.querySelector("#search-input"),
    category: document.querySelector("#category-filter"),
    sort: document.querySelector("#sort-select"),
    articleList: document.querySelector("#article-list"),
    resultCount: document.querySelector("#result-count")
};

let articles = [];
let activeRequest = 0;

function createElement(tag, className = "", text = "") {
    const element = document.createElement(tag);

    if (className) {
        element.className = className;
    }

    element.textContent = text;

    return element;
}

async function fetchData(url) {
    const response = await fetch(url, {
        cache: "no-store"
    });

    if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || "Tietojen hakeminen epäonnistui.");
    }

    return response.json();
}

function formatReportName(id) {
    const match = id.match(
        /^learning-report-(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})/
    );

    if (!match) {
        return id;
    }

    const [, year, month, day, hour, minute] = match;

    return `${day}.${month}.${year} klo ${hour}:${minute}`;
}

function formatDate(value) {
    if (!value) {
        return "Ajankohta ei tiedossa";
    }

    const date = new Date(value);

    if (value.includes("T") && !Number.isNaN(date.getTime())) {
        return date.toLocaleString("fi-FI", {
            dateStyle: "medium",
            timeStyle: "short"
        });
    }

    return value;
}

function formatPublished(value) {
    if (!value) {
        return "";
    }

    const date = new Date(value);

    return Number.isNaN(date.getTime())
        ? value
        : date.toLocaleDateString("fi-FI");
}

function safeUrl(value) {
    if (typeof value !== "string") {
        return null;
    }

    try {
        const url = new URL(value);

        if (
            url.protocol === "https:" &&
            url.hostname &&
            !url.username &&
            !url.password
        ) {
            return url.href;
        }
    } catch {
        return null;
    }

    return null;
}

function renderChart(container, values, total) {
    container.replaceChildren();

    for (const [name, count] of Object.entries(values)) {
        const item = createElement("div", "chart-item");
        const label = createElement("div", "chart-label");

        label.append(
            createElement("span", "", name),
            createElement("span", "", String(count))
        );

        const track = createElement("div", "chart-track");
        const bar = createElement("div", "chart-bar");

        const percentage = total > 0
            ? Math.min(100, Math.max(0, count / total * 100))
            : 0;

        bar.style.width = `${percentage}%`;

        track.setAttribute("aria-hidden", "true");
        track.append(bar);
        item.append(label, track);
        container.append(item);
    }
}

function renderStatistics(stats) {
    elements.articleCount.textContent = stats.article_count;
    elements.sourceCount.textContent = stats.source_count;
    elements.categoryCount.textContent = stats.category_count;

    elements.averageRating.textContent =
        stats.average_rating === null
            ? "–"
            : `${stats.average_rating.toLocaleString("fi-FI", {
                minimumFractionDigits: 1,
                maximumFractionDigits: 1
            })} / 5`;

    renderChart(
        elements.categoryChart,
        stats.categories,
        stats.article_count
    );

    renderChart(
        elements.sourceChart,
        stats.sources,
        stats.article_count
    );
}

function renderCategoryOptions() {
    const categories = [
        ...new Set(articles.map(article => article.category))
    ].sort((a, b) => a.localeCompare(b, "fi"));

    elements.category.replaceChildren(
        new Option("Kaikki aihealueet", "")
    );

    for (const category of categories) {
        elements.category.add(new Option(category, category));
    }
}

function createDetailBlock(title, content, className = "") {
    const block = createElement("div", "detail-block");

    block.append(
        createElement("h4", "", title),
        createElement("p", className, content || "Ei tietoa.")
    );

    return block;
}

function createArticleCard(article) {
    const card = createElement("article", "article-card");
    const meta = createElement("div", "article-meta");

    const category = createElement(
        "span",
        "category-badge",
        article.category
    );

    const rating = createElement("span", "rating");

    if (
        Number.isInteger(article.rating) &&
        article.rating >= 1 &&
        article.rating <= 5
    ) {
        rating.textContent =
            "★".repeat(article.rating) +
            "☆".repeat(5 - article.rating);

        rating.setAttribute(
            "aria-label",
            `Hyödyllisyys ${article.rating} / 5`
        );
    } else {
        rating.textContent = "Ei arviota";
    }

    meta.append(category, rating);

    const title = createElement("h3", "", article.title);

    const sourceText = [
        article.source,
        formatPublished(article.published)
    ].filter(Boolean).join(" · ");

    const source = createElement(
        "p",
        "article-source",
        sourceText
    );

    const summary = createElement(
        "p",
        "article-summary",
        article.summary || "Tiivistelmää ei ole saatavilla."
    );

    const skills = createElement("div", "skills");

    for (const skill of article.skills || []) {
        skills.append(
            createElement("span", "skill-tag", skill)
        );
    }

    const details = createElement("details", "article-details");

    details.append(
        createElement("summary", "", "Oppimisanalyysi"),
        createDetailBlock("Hyöty", article.benefit),
        createDetailBlock("Oppimisehdotus", article.learning_suggestion),
        createDetailBlock("Hyödyllisyyden perustelu", article.usefulness)
    );

    if (!article.summary && article.raw_analysis) {
        details.append(
            createDetailBlock(
                "Alkuperäinen analyysi",
                article.raw_analysis,
                "raw-analysis"
            )
        );
    }

    card.append(meta, title, source, summary, skills, details);

    const url = safeUrl(article.url);

    if (url) {
        const link = createElement(
            "a",
            "article-link",
            "Lue alkuperäinen artikkeli ↗"
        );

        link.href = url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";

        card.append(link);
    }

    return card;
}

function renderArticles() {
    const search = elements.search.value.trim().toLocaleLowerCase("fi");
    const category = elements.category.value;
    const sort = elements.sort.value;

    const filtered = articles.filter(article => {
        const matchesCategory =
            !category || article.category === category;

        const searchableText = [
            article.title,
            article.source,
            article.category,
            article.summary,
            article.benefit,
            article.learning_suggestion,
            ...(article.skills || [])
        ].join(" ").toLocaleLowerCase("fi");

        return matchesCategory && searchableText.includes(search);
    });

    if (sort === "rating") {
        filtered.sort(
            (a, b) => (b.rating ?? 0) - (a.rating ?? 0)
        );
    } else if (sort === "title") {
        filtered.sort(
            (a, b) => a.title.localeCompare(b.title, "fi")
        );
    }

    elements.resultCount.textContent =
        `${filtered.length} / ${articles.length} artikkelia`;

    elements.articleList.replaceChildren();

    if (!filtered.length) {
        elements.articleList.append(
            createElement(
                "p",
                "empty-message",
                "Hakuehtoja vastaavia artikkeleita ei löytynyt."
            )
        );

        return;
    }

    const fragment = document.createDocumentFragment();

    for (const article of filtered) {
        fragment.append(createArticleCard(article));
    }

    elements.articleList.append(fragment);
}

async function loadReport(id) {
    const requestId = ++activeRequest;

    elements.status.textContent = "Ladataan raporttia...";
    elements.dashboard.hidden = true;

    try {
        const data = await fetchData(
            `/api/report?id=${encodeURIComponent(id)}`
        );

        if (requestId !== activeRequest) {
            return;
        }

        articles = data.articles;

        elements.reportDate.textContent =
            `Raportti luotu: ${formatDate(data.created_at)}`;

        elements.search.value = "";
        elements.sort.value = "default";

        renderStatistics(data.statistics);
        renderCategoryOptions();
        renderArticles();

        elements.status.textContent = "";
        elements.dashboard.hidden = false;

    } catch (error) {
        if (requestId !== activeRequest) {
            return;
        }

        elements.reportDate.textContent = "Raportti ei ole saatavilla";
        elements.status.textContent = error.message;
    }
}

async function initialize() {
    elements.status.textContent = "Haetaan raportteja...";

    try {
        const reports = await fetchData("/api/reports");

        if (!reports.length) {
            elements.reportDate.textContent = "Ei raportteja";
            elements.status.textContent =
                "Raportteja ei vielä löytynyt. Käynnistä ensin main.py.";

            return;
        }

        elements.reportSelect.replaceChildren();

        for (const report of reports) {
            elements.reportSelect.add(
                new Option(formatReportName(report.id), report.id)
            );
        }

        elements.reportSelect.disabled = false;

        await loadReport(reports[0].id);

    } catch (error) {
        elements.reportDate.textContent = "Raportteja ei voitu hakea";
        elements.status.textContent = error.message;
    }
}

elements.reportSelect.addEventListener("change", () => {
    loadReport(elements.reportSelect.value);
});

elements.search.addEventListener("input", renderArticles);
elements.category.addEventListener("change", renderArticles);
elements.sort.addEventListener("change", renderArticles);

initialize();
