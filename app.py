"""
Student Performance Dashboard — Flask backend.

Accepts an uploaded CSV of student marks, computes aggregate and
per-subject statistics with Pandas, and returns JSON for the
Chart.js-powered frontend to render.

Expected CSV shape (flexible column order, case-insensitive):
    name, <subject_1>, <subject_2>, ..., <subject_n>
Any non-numeric column other than a name/id column is ignored.
"""

import io
import re

import pandas as pd
from flask import Flask, jsonify, render_template, request

# On Vercel, files in public/** are served directly from the CDN at the
# root path (e.g. public/css/style.css -> /css/style.css). Configuring
# Flask's static handling to match means the exact same URLs also work
# when running locally with `python app.py`.
app = Flask(__name__, static_folder="public", static_url_path="")

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB guardrail
NAME_COLUMN_CANDIDATES = {"name", "student", "student_name", "student name", "id"}


def _find_name_column(columns):
    lowered = {c.lower().strip(): c for c in columns}
    for candidate in NAME_COLUMN_CANDIDATES:
        if candidate in lowered:
            return lowered[candidate]
    return None


def _clean_numeric(series: pd.Series) -> pd.Series:
    """Coerce a column to numeric, stripping stray % signs / whitespace."""
    if series.dtype == object:
        series = series.astype(str).str.replace("%", "", regex=False).str.strip()
    return pd.to_numeric(series, errors="coerce")


def compute_dashboard_payload(df: pd.DataFrame) -> dict:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    name_col = _find_name_column(df.columns)
    subject_cols = []
    for col in df.columns:
        if col == name_col:
            continue
        numeric = _clean_numeric(df[col])
        # Treat as a "subject" if at least half the cells parse as numbers
        if numeric.notna().sum() >= max(1, len(numeric) * 0.5):
            df[col] = numeric
            subject_cols.append(col)

    if not subject_cols:
        raise ValueError(
            "No numeric mark columns were found. Make sure your CSV has at "
            "least one column of numeric scores."
        )

    df["__overall__"] = df[subject_cols].mean(axis=1, skipna=True)

    overall = df["__overall__"].dropna()
    total_students = int(len(df))
    average_marks = round(float(overall.mean()), 2) if len(overall) else 0
    highest_marks = round(float(overall.max()), 2) if len(overall) else 0
    lowest_marks = round(float(overall.min()), 2) if len(overall) else 0

    # Score distribution buckets (used for the pie/donut chart)
    bins = [-1, 59, 69, 79, 89, 100]
    labels = ["Below 60", "60-69", "70-79", "80-89", "90-100"]
    dist_series = pd.cut(overall, bins=bins, labels=labels)
    distribution = {label: int((dist_series == label).sum()) for label in labels}

    # Per-subject stats
    subjects = []
    for col in subject_cols:
        col_series = df[col].dropna()
        if col_series.empty:
            continue
        subjects.append(
            {
                "subject": col,
                "average": round(float(col_series.mean()), 2),
                "highest": round(float(col_series.max()), 2),
                "lowest": round(float(col_series.min()), 2),
            }
        )

    # At-risk students: overall average below 60
    at_risk = df[df["__overall__"] < 60]
    at_risk_count = int(len(at_risk))

    # Top performer
    top_row = df.loc[df["__overall__"].idxmax()] if len(overall) else None
    top_performer = None
    if top_row is not None:
        top_performer = {
            "name": str(top_row[name_col]) if name_col else f"Student {int(top_row.name) + 1}",
            "average": round(float(top_row["__overall__"]), 2),
        }

    # Full table for the data grid — replace NaN with None for valid JSON
    table_cols = ([name_col] if name_col else []) + subject_cols
    table = df[table_cols].where(pd.notnull(df[table_cols]), None).to_dict(orient="records")
    if not name_col:
        for i, row in enumerate(table):
            row["Name"] = f"Student {i + 1}"

    return {
        "summary": {
            "total_students": total_students,
            "average_marks": average_marks,
            "highest_marks": highest_marks,
            "lowest_marks": lowest_marks,
            "at_risk_count": at_risk_count,
            "top_performer": top_performer,
        },
        "subjects": subjects,
        "distribution": distribution,
        "table": table,
        "table_columns": (["Name"] if not name_col else [name_col]) + subject_cols,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "Please upload a .csv file."}), 400

    raw = file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        return jsonify({"error": "File is too large (5 MB limit)."}), 400

    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Could not parse CSV: {exc}"}), 400

    if df.empty:
        return jsonify({"error": "The uploaded CSV has no rows."}), 400

    try:
        payload = compute_dashboard_payload(df)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(payload)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
