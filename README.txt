STUDENT PERFORMANCE DASHBOARD — Flask Web App
================================================

Uses: Python, Flask, Pandas, NumPy, Matplotlib

RUN LOCALLY
-----------
1. Open terminal in this folder
2. Install dependencies:
   pip install -r requirements.txt

3. Run the app:
   python local_app.py

4. Open your browser and go to:
   http://127.0.0.1:5000

DEPLOY ON VERCEL
-----------------
Previous version failed on Vercel with:
  ModuleNotFoundError: No module named 'numpy'
because Vercel auto-detected the root-level app.py as a serverless function
(it looks for any top-level .py file exposing a Flask "app" object) and
built/ran THAT instead of, or alongside, api/index.py — so the dependency
install from requirements.txt never got wired to the function that Vercel
actually invoked at request time.

FIX APPLIED:
  - Renamed the root file to local_app.py (for local dev only — Vercel's
    auto-detector only looks for files literally named app.py / index.py
    at specific locations, so this removes the ambiguity entirely).
  - api/index.py is now the ONLY Python entrypoint in the whole project,
    and it's fully self-contained (the entire Flask app is defined right
    there, not imported from another file), so there is zero cross-file
    import ambiguity for Vercel's builder to get confused by.
  - api/index.py explicitly points Flask's template_folder and
    static_folder back up to the project root's templates/ and static/
    directories, since the entrypoint now lives one level deeper
    (api/) than before.
  - Added .vercelignore excluding local_app.py so it's never even
    uploaded as part of the deployed bundle.
  - vercel.json's "builds" array still explicitly targets api/index.py,
    but now there's nothing else for Vercel to mistakenly build instead.

Steps to deploy:
1. Push this folder to a GitHub repo (or run `vercel` from inside this
   folder using the Vercel CLI).
2. Import the repo in Vercel (New Project -> Import).
3. Vercel auto-detects Python via vercel.json + requirements.txt. No extra
   build settings needed. Click Deploy.
4. Your dashboard will be live at the generated *.vercel.app URL.

If you had a PREVIOUS Vercel project already created for this app, delete
that project (or clear its build cache) before redeploying this fixed
version — stale build settings/cache from the old broken structure can
otherwise persist and cause the same error again even with corrected files.

Note: Vercel functions are stateless/ephemeral, and session data uses
Flask's signed cookie sessions (no server-side file storage), so
"Add Student" / "Upload CSV" data persists per-browser via cookies and
works fine on Vercel.

FOLDER STRUCTURE
-----------------
student_dashboard/
  local_app.py             -> Use this to run locally (python local_app.py)
  api/
    index.py                -> Vercel entrypoint. Full, self-contained Flask
                                app (Pandas + NumPy + Matplotlib + CSV upload).
                                This is the ONLY file Vercel builds/runs.
  templates/
    index.html               -> Page template (Jinja2), dark/light mode CSS
  static/
    sample_students.csv       -> Ready-made sample CSV (10 students)
    sample_students_blank_template.csv -> Blank template with just headers
  requirements.txt           -> Python dependencies (pinned versions)
  vercel.json                -> Vercel routing/build config
  .vercelignore              -> Excludes local_app.py from deployment

FEATURES
--------
- Pandas DataFrame stores and manages student records
- NumPy used for Total/Average calculation, grade assignment (np.select),
  and trendline fitting (np.polyfit) on the scatter chart
- Matplotlib renders 4 charts server-side (subject averages, top 5 students,
  grade distribution pie, attendance vs marks scatter with trendline)
- Charts are transparent PNGs (base64-embedded) so they look correct in
  both light and dark mode
- Add / delete students via web form; data persists in your browser session
- CSV UPLOAD: upload a .csv with columns Student, Math, Science, English,
  Attendance to bulk-load students. Choose "Replace all" or "Add to existing".
  Invalid rows are skipped with a warning; missing required columns show a
  clear error message instead of crashing.
- Two ready-made CSVs included in static/: a filled sample (10 students) and
  a blank template (headers only). Also downloadable in-app from the sidebar
  link, or directly at /sample_students.csv (generated dynamically by Flask).
- DARK / LIGHT MODE: toggle in the top-left of the sidebar (☀ / ☾). Choice is
  saved in a cookie so it persists across visits. Charts adapt text color
  automatically to stay readable in both themes.
- "Reset to Sample Data" and "Clear All" buttons included

CSV FORMAT REQUIRED
--------------------
Student,Math,Science,English,Attendance
Aman,85,80,88,95
...

- Column names are matched case-insensitively and whitespace-trimmed.
- Math/Science/English/Attendance are clamped to the 0-100 range.
- Rows with missing/invalid numeric values are skipped (not crashed on),
  and you'll see a summary message of how many rows were skipped.

TESTED
------
Before packaging, this fixed version was verified end-to-end against the
actual api/index.py entrypoint (the one Vercel runs), covering: home page +
chart rendering, adding a student, dark/light theme toggling with correct
data-theme attribute, sample CSV download, CSV upload, static file serving
from the corrected template/static paths, and local_app.py still working
standalone for local development. All passed.
