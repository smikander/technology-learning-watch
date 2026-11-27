
import json
import pytest

import dashboard_data
from app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(dashboard_data, "REPORT_DIR", tmp_path)
    monkeypatch.setitem(app.config, "TESTING", True)

    with app.test_client() as client:
        yield client


@pytest.fixture
def report_file(tmp_path):
    path = tmp_path / "learning-report-2026-11-24.json"

    path.write_text(
        json.dumps({
            "created_at": "2026-11-24T19:18:00",
            "articles": [{
                "title": "Python Testing",
                "source": "Python Insider",
                "category": "Python",
                "published": "2026-11-24",
                "url": "https://example.com",
                "analysis": "Hyödyllisyys: 4 – Hyödyllinen."
            }]
        }),
        encoding="utf-8"
    )

    return path


def test_index(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Technology & Learning Watch" in response.data


def test_empty_report_list(client):
    response = client.get("/api/reports")

    assert response.status_code == 200
    assert response.get_json() == []


def test_report_list(client, report_file):
    response = client.get("/api/reports")

    assert response.status_code == 200
    assert response.get_json() == [{
        "id": report_file.stem,
        "filename": report_file.name
    }]


def test_latest_report(client, report_file):
    response = client.get("/api/report")

    assert response.status_code == 200

    data = response.get_json()

    assert data["statistics"]["article_count"] == 1
    assert data["articles"][0]["rating"] == 4


def test_selected_report(client, report_file):
    response = client.get(
        "/api/report",
        query_string={"id": report_file.stem}
    )

    assert response.status_code == 200


def test_no_reports(client):
    response = client.get("/api/report")

    assert response.status_code == 404
    assert "error" in response.get_json()


def test_unknown_report(client, report_file):
    response = client.get("/api/report?id=unknown")

    assert response.status_code == 404


@pytest.mark.parametrize("report_id", [
    "../../config.json",
    "../main.py",
    "/etc/passwd",
    "C:/Windows/win.ini"
])
def test_path_traversal(client, report_file, report_id):
    response = client.get(
        "/api/report",
        query_string={"id": report_id}
    )

    assert response.status_code == 404


def test_corrupted_report(client, tmp_path):
    path = tmp_path / "learning-report-corrupted.json"
    path.write_text("invalid json", encoding="utf-8")

    response = client.get("/api/report")

    assert response.status_code == 500
    assert "error" in response.get_json()
