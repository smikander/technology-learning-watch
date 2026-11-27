
from flask import Flask, render_template, jsonify, request

from dashboard_data import list_reports, load_report

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/reports")
def get_reports():
    reports = list_reports()

    return jsonify([
        {
            "id": path.stem,
            "filename": path.name
        }
        for path in reports
    ])


@app.get("/api/report")
def get_report():
    reports = list_reports()

    if not reports:
        return jsonify({
            "error": "Raportteja ei löytynyt."
        }), 404

    report_id = request.args.get("id")

    if report_id:
        selected_report = next(
            (path for path in reports if path.stem == report_id),
            None
        )
    else:
        selected_report = reports[0]

    if selected_report is None:
        return jsonify({
            "error": "Valittua raporttia ei löytynyt."
        }), 404

    try:
        return jsonify(load_report(selected_report))

    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        app.logger.exception("Raportin lukeminen epäonnistui")

        return jsonify({
            "error": "Raportin lukeminen epäonnistui."
        }), 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
