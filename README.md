# Smart Expense Splitting App (Frontend + Flask Backend)

Quick start:
1. Create and activate a Python virtualenv:
   - Windows (PowerShell):
     ```
     python -m venv venv
     .\venv\Scripts\activate
     ```
     - macOS / Linux:
     ```
     python -m venv venv
     source venv/bin/activate
     ```
2. Install dependencies:
   ```
   pip install -r backend/requirements.txt
   ```
3. (Optional) Initialize DB:
   ```
   python backend/db_init.py
   ```
   The backend will auto-create DB on first run if missing.
4. Run app:
   ```
   python backend/app.py
   ```
5. Open in browser:
   - http://localhost:5000

Features: create groups & members, add expenses (equal or custom shares), view balances.
