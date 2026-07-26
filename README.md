# Gradeline — Student Performance Dashboard

A Flask + Pandas + Chart.js web app that turns a class roster CSV into
instant statistics, charts, and a searchable data table.

## Run it locally

```bash
cd student-performance-dashboard
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

## Using it

1. Drop a `.csv` file onto the upload panel (or click "Try sample data").
2. The CSV needs one name/id column plus any number of numeric score columns
   — column names and order don't matter (e.g. `Name, Math, Science, English`).
3. Gradeline computes:
   - Total students, average / highest / lowest overall marks
   - At-risk count (students averaging below 60) and the top performer
   - Per-subject average / highest / lowest
   - A score-distribution breakdown (below 60, 60s, 70s, 80s, 90-100)
   - A full sortable/searchable roster table
4. Click **Upload a different file** to reset and try another CSV.

## Deploying to Vercel

Vercel auto-detects the Flask `app` instance in `app.py` — no `builds`/`routes`
config needed. The included `vercel.json` just sets a function timeout:

```bash
npm i -g vercel
vercel
```

Static assets (`css/`, `js/`, `sample_students.csv`) live in `public/**`,
which Vercel serves directly from its CDN. Locally, Flask is configured to
serve that same folder at the same root-level paths, so the app behaves
identically in both places.

## Project structure

```
student-performance-dashboard/
├── app.py                  # Flask server, routes, Pandas logic
├── requirements.txt        # Python dependencies
├── vercel.json             # Vercel function config (zero-config detection)
├── public/
│   ├── css/style.css       # Dashboard styling (light + dark themes)
│   ├── js/main.js          # Chart.js + upload/table/theme logic
│   └── sample_students.csv # Sample data for quick demos
└── templates/
    └── index.html          # Dashboard layout
```

## Notes

- Files are capped at 5 MB and validated server-side before parsing.
- CSVs missing a name column still work — rows are labeled "Student 1, 2, …".
- Everything renders client-side after upload, so switching files never
  requires a page reload.
