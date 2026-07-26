"""
Student Performance Dashboard — Flask Web App
Uses NumPy for numeric ops, Pandas for data handling,
Matplotlib for server-side chart rendering.
Now with CSV upload and dark/light mode toggle.
"""

import io
import os
import csv
import base64
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # server-side rendering, no display needed
import matplotlib.pyplot as plt

from flask import (
    Flask, render_template, request, redirect, url_for, session,
    make_response, flash, Response
)

# api/index.py lives one directory below the project root, but templates/
# and static/ live at the project root. Point Flask at them explicitly so
# render_template() and url_for('static', ...) resolve correctly on Vercel.
_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TEMPLATE_DIR = os.path.join(_ROOT_DIR, "templates")
_STATIC_DIR = os.path.join(_ROOT_DIR, "static")

app = Flask(__name__, template_folder=_TEMPLATE_DIR, static_folder=_STATIC_DIR)
app.secret_key = "student-dashboard-secret-key"

REQUIRED_COLUMNS = ["Student", "Math", "Science", "English", "Attendance"]

# ---------------------------------------------------------
# Default sample dataset
# ---------------------------------------------------------
SAMPLE_DATA = [
    {"Student": "Aman", "Math": 85, "Science": 80, "English": 88, "Attendance": 95},
    {"Student": "Priya", "Math": 92, "Science": 89, "English": 84, "Attendance": 98},
    {"Student": "Rahul", "Math": 78, "Science": 75, "English": 82, "Attendance": 85},
    {"Student": "Sneha", "Math": 65, "Science": 70, "English": 68, "Attendance": 70},
    {"Student": "Vikas", "Math": 90, "Science": 85, "English": 79, "Attendance": 92},
    {"Student": "Anjali", "Math": 55, "Science": 60, "English": 58, "Attendance": 65},
    {"Student": "Rohit", "Math": 72, "Science": 78, "English": 74, "Attendance": 80},
    {"Student": "Kavya", "Math": 88, "Science": 91, "English": 85, "Attendance": 96},
    {"Student": "Suresh", "Math": 60, "Science": 65, "English": 62, "Attendance": 68},
    {"Student": "Neha", "Math": 95, "Science": 93, "English": 90, "Attendance": 99},
]

COLORS = {
    "primary": "#065A82",
    "secondary": "#1C7293",
    "accent": "#E8823C",
    "purple": "#8172B2",
    "grade": {"A+": "#2FBF71", "A": "#4C9BD9", "B": "#E8B23C", "C": "#E8823C", "D": "#D9534F"},
}


def get_data():
    """Fetch current dataset from session, or fall back to sample data."""
    if "data" not in session:
        session["data"] = SAMPLE_DATA
    return session["data"]


def build_dataframe(records):
    """Build a Pandas DataFrame and compute Total/Average/Grade using NumPy."""
    df = pd.DataFrame(records)
    if df.empty:
        return df

    # NumPy used directly for the numeric aggregation
    marks = df[["Math", "Science", "English"]].to_numpy(dtype=float)
    df["Total"] = np.sum(marks, axis=1)
    df["Average"] = np.round(np.mean(marks, axis=1), 1)

    # Grade assignment via NumPy vectorized select
    conditions = [
        df["Average"] >= 90,
        df["Average"] >= 80,
        df["Average"] >= 70,
        df["Average"] >= 60,
    ]
    choices = ["A+", "A", "B", "C"]
    df["Grade"] = np.select(conditions, choices, default="D")

    return df


def fig_to_base64(fig, dark=False):
    """Render a Matplotlib figure to a base64 PNG string for embedding in HTML."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight",
                transparent=True)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def make_charts(df, dark=False):
    """Generate all 4 Matplotlib charts and return them as base64 strings."""
    if df.empty:
        return {}

    charts = {}

    text_color = "#E7EEF3" if dark else "#0B1E2D"
    grid_color = "#2A3B47" if dark else "#D7E3EA"

    def style_axes(ax):
        ax.tick_params(colors=text_color, labelsize=9)
        ax.xaxis.label.set_color(text_color)
        ax.yaxis.label.set_color(text_color)
        ax.title.set_color(text_color)
        for spine in ax.spines.values():
            spine.set_color(grid_color)

    # --- Chart 1: Subject-wise Average (Bar) ---
    subject_avg = np.mean(df[["Math", "Science", "English"]].to_numpy(dtype=float), axis=0)
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    bars = ax.bar(["Math", "Science", "English"], subject_avg,
                   color=[COLORS["primary"], COLORS["secondary"], COLORS["accent"]])
    ax.set_ylim(0, 100)
    ax.set_ylabel("Average Marks")
    ax.set_title("Subject-wise Average Marks", fontsize=11, fontweight="bold")
    for b, v in zip(bars, subject_avg):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.1f}", ha="center", fontsize=9, color=text_color)
    ax.spines[["top", "right"]].set_visible(False)
    style_axes(ax)
    plt.tight_layout()
    charts["subject_avg"] = fig_to_base64(fig, dark)

    # --- Chart 2: Top 5 by Total (Horizontal Bar) ---
    top5 = df.sort_values("Total", ascending=False).head(5)
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    ax.barh(top5["Student"], top5["Total"], color=COLORS["purple"])
    ax.invert_yaxis()
    ax.set_xlabel("Total Marks")
    ax.set_title("Top 5 Students by Total Marks", fontsize=11, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    style_axes(ax)
    plt.tight_layout()
    charts["top5"] = fig_to_base64(fig, dark)

    # --- Chart 3: Grade Distribution (Pie) ---
    grade_counts = df["Grade"].value_counts()
    colors = [COLORS["grade"].get(g, "#999") for g in grade_counts.index]
    fig, ax = plt.subplots(figsize=(4.6, 3.8))
    wedges, texts, autotexts = ax.pie(
        grade_counts.values, labels=grade_counts.index, autopct="%1.1f%%",
        startangle=90, colors=colors, wedgeprops={"edgecolor": "white", "linewidth": 1.5})
    for t in texts:
        t.set_color(text_color)
    ax.set_title("Grade Distribution", fontsize=11, fontweight="bold", color=text_color)
    plt.tight_layout()
    charts["grade_dist"] = fig_to_base64(fig, dark)

    # --- Chart 4: Attendance vs Average (Scatter) ---
    fig, ax = plt.subplots(figsize=(5.2, 3.8))
    ax.scatter(df["Attendance"], df["Average"], color=COLORS["accent"], s=70, zorder=3)
    for _, row in df.iterrows():
        ax.annotate(row["Student"], (row["Attendance"] + 0.4, row["Average"]), fontsize=8, color=text_color)
    # NumPy trendline
    if len(df) >= 2:
        z = np.polyfit(df["Attendance"], df["Average"], 1)
        trend_x = np.linspace(df["Attendance"].min(), df["Attendance"].max(), 50)
        ax.plot(trend_x, np.polyval(z, trend_x), "--", color=COLORS["primary"], alpha=0.8, linewidth=1.5)
    ax.set_xlabel("Attendance (%)")
    ax.set_ylabel("Average Marks")
    ax.set_title("Attendance vs Average Marks", fontsize=11, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    style_axes(ax)
    plt.tight_layout()
    charts["scatter"] = fig_to_base64(fig, dark)

    return charts


def get_theme():
    return request.cookies.get("theme", "light")


def parse_csv_records(file_storage):
    """Parse an uploaded CSV file into a list of student record dicts.
    Returns (records, error_message)."""
    try:
        raw = file_storage.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        return None, "Could not read the file. Please upload a UTF-8 encoded CSV."

    if not raw.strip():
        return None, "The uploaded CSV is empty."

    reader = csv.DictReader(io.StringIO(raw))
    if reader.fieldnames is None:
        return None, "The uploaded CSV has no header row."

    # Normalize header names (strip whitespace, match case-insensitively)
    normalized_map = {}
    for original in reader.fieldnames:
        key = original.strip()
        for req in REQUIRED_COLUMNS:
            if key.lower() == req.lower():
                normalized_map[original] = req
                break

    missing = [c for c in REQUIRED_COLUMNS if c not in normalized_map.values()]
    if missing:
        return None, (f"CSV is missing required column(s): {', '.join(missing)}. "
                       f"Expected columns: {', '.join(REQUIRED_COLUMNS)}.")

    records = []
    errors = []
    for i, row in enumerate(reader, start=2):  # row 1 is header
        try:
            name = row[[k for k, v in normalized_map.items() if v == "Student"][0]].strip()
            if not name:
                continue
            record = {"Student": name}
            for col in ["Math", "Science", "English", "Attendance"]:
                src_key = [k for k, v in normalized_map.items() if v == col][0]
                val = row[src_key]
                if val is None or str(val).strip() == "":
                    raise ValueError(f"missing {col}")
                num = int(float(val))
                num = max(0, min(100, num))
                record[col] = num
            records.append(record)
        except (ValueError, KeyError, IndexError):
            errors.append(f"Row {i} skipped (invalid or missing data).")

    if not records:
        return None, "No valid student rows found in the CSV. " + " ".join(errors[:5])

    return records, ("; ".join(errors[:5]) if errors else None)


@app.route("/")
def index():
    records = get_data()
    df = build_dataframe(records)
    theme = get_theme()
    charts = make_charts(df, dark=(theme == "dark"))

    if df.empty:
        stats = {"count": 0, "avg": 0, "top": "—", "attendance": 0}
        table = []
    else:
        stats = {
            "count": int(len(df)),
            "avg": round(float(np.mean(df["Average"])), 1),
            "top": df.loc[df["Total"].idxmax(), "Student"],
            "attendance": round(float(np.mean(df["Attendance"])), 0),
        }
        table = df.sort_values("Total", ascending=False).to_dict("records")

    return render_template("index.html", stats=stats, table=table, charts=charts,
                            grade_colors=COLORS["grade"], theme=theme)


@app.route("/add", methods=["POST"])
def add_student():
    records = get_data()
    try:
        new_student = {
            "Student": request.form["name"].strip(),
            "Math": int(request.form["math"]),
            "Science": int(request.form["science"]),
            "English": int(request.form["english"]),
            "Attendance": int(request.form["attendance"]),
        }
        if new_student["Student"]:
            records.append(new_student)
            session["data"] = records
    except (ValueError, KeyError):
        pass
    return redirect(url_for("index"))


@app.route("/upload", methods=["POST"])
def upload_csv():
    file = request.files.get("csv_file")
    if not file or file.filename == "":
        flash("Please choose a CSV file to upload.", "error")
        return redirect(url_for("index"))

    if not file.filename.lower().endswith(".csv"):
        flash("Only .csv files are supported.", "error")
        return redirect(url_for("index"))

    records, message = parse_csv_records(file)
    if records is None:
        flash(message or "Could not process the CSV file.", "error")
        return redirect(url_for("index"))

    mode = request.form.get("upload_mode", "replace")
    if mode == "append":
        existing = get_data()
        session["data"] = existing + records
        flash(f"Added {len(records)} student(s) from CSV.", "success")
    else:
        session["data"] = records
        flash(f"Loaded {len(records)} student(s) from CSV.", "success")

    if message:
        flash(message, "warning")

    return redirect(url_for("index"))


@app.route("/delete/<int:index>", methods=["POST"])
def delete_student(index):
    records = get_data()
    if 0 <= index < len(records):
        records.pop(index)
        session["data"] = records
    return redirect(url_for("index"))


@app.route("/reset", methods=["POST"])
def reset_data():
    session["data"] = SAMPLE_DATA
    return redirect(url_for("index"))


@app.route("/clear", methods=["POST"])
def clear_data():
    session["data"] = []
    return redirect(url_for("index"))


@app.route("/theme/<mode>", methods=["POST"])
def set_theme(mode):
    if mode not in ("light", "dark"):
        mode = "light"
    resp = make_response(redirect(url_for("index")))
    resp.set_cookie("theme", mode, max_age=60 * 60 * 24 * 365)
    return resp


@app.route("/sample_students.csv")
def sample_csv():
    """Serve a ready-made sample CSV for users to download and try."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=REQUIRED_COLUMNS)
    writer.writeheader()
    for row in SAMPLE_DATA:
        writer.writerow(row)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=sample_students.csv"}
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
