from flask import Flask, jsonify, request, send_from_directory
import sqlite3, os
from flask_cors import CORS

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "expenses.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

if not os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS groups (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS members (id INTEGER PRIMARY KEY AUTOINCREMENT, group_id INTEGER NOT NULL, name TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, group_id INTEGER NOT NULL, title TEXT, amount REAL NOT NULL, payer_id INTEGER NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS splits (id INTEGER PRIMARY KEY AUTOINCREMENT, expense_id INTEGER NOT NULL, member_id INTEGER NOT NULL, share REAL NOT NULL);
    ''')
    conn.commit()
    conn.close()

app = Flask(__name__, static_folder="../frontend", static_url_path="/")
CORS(app)

def row_to_dict(row):
    return dict(row) if row else None

@app.route("/api/groups", methods=["GET"])
def list_groups():
    conn = get_db()
    rows = conn.execute("SELECT * FROM groups ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify([row_to_dict(r) for r in rows])

@app.route("/api/groups", methods=["POST"])
def create_group():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error":"Name required"}), 400
    conn = get_db()
    cur = conn.execute("INSERT INTO groups (name) VALUES (?)", (name,))
    conn.commit()
    gid = cur.lastrowid
    row = conn.execute("SELECT * FROM groups WHERE id=?", (gid,)).fetchone()
    conn.close()
    return jsonify(row_to_dict(row)), 201

@app.route("/api/groups/<int:gid>/members", methods=["GET"])
def list_members(gid):
    conn = get_db()
    rows = conn.execute("SELECT * FROM members WHERE group_id=? ORDER BY id", (gid,)).fetchall()
    conn.close()
    return jsonify([row_to_dict(r) for r in rows])

@app.route("/api/groups/<int:gid>/members", methods=["POST"])
def add_member(gid):
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error":"Name required"}), 400
    conn = get_db()
    cur = conn.execute("INSERT INTO members (group_id, name) VALUES (?,?)", (gid, name))
    conn.commit()
    mid = cur.lastrowid
    row = conn.execute("SELECT * FROM members WHERE id=?", (mid,)).fetchone()
    conn.close()
    return jsonify(row_to_dict(row)), 201

@app.route("/api/groups/<int:gid>/expenses", methods=["GET"])
def list_expenses(gid):
    conn = get_db()
    rows = conn.execute("SELECT e.*, m.name as payer_name FROM expenses e JOIN members m ON e.payer_id=m.id WHERE e.group_id=? ORDER BY e.id DESC", (gid,)).fetchall()
    data = []
    for r in rows:
        expense = dict(r)
        splits = conn.execute("SELECT s.*, mem.name as member_name FROM splits s JOIN members mem ON s.member_id=mem.id WHERE s.expense_id=?", (r["id"],)).fetchall()
        expense["splits"] = [dict(s) for s in splits]
        data.append(expense)
    conn.close()
    return jsonify(data)

@app.route("/api/groups/<int:gid>/expenses", methods=["POST"])
def add_expense(gid):
    data = request.get_json() or {}
    title = data.get("title","").strip()
    try:
        amount = float(data.get("amount",0))
    except:
        return jsonify({"error":"Invalid amount"}), 400
    payer = data.get("payer_id")
    splits = data.get("splits") or []
    equal = bool(data.get("equal_split", True))

    if not payer:
        return jsonify({"error":"Payer required"}), 400
    if amount <= 0:
        return jsonify({"error":"Amount must be > 0"}), 400
    conn = get_db()
    cur = conn.execute("INSERT INTO expenses (group_id, title, amount, payer_id) VALUES (?,?,?,?)", (gid, title, amount, payer))
    conn.commit()
    expense_id = cur.lastrowid
    if equal:
        members = conn.execute("SELECT id FROM members WHERE group_id=?", (gid,)).fetchall()
        member_ids = [m["id"] for m in members]
        if not member_ids:
            conn.close()
            return jsonify({"error":"No members in group"}), 400
        share = round(amount/len(member_ids), 2)
        for mid in member_ids:
            conn.execute("INSERT INTO splits (expense_id, member_id, share) VALUES (?,?,?)", (expense_id, mid, share))
    else:
        for s in splits:
            conn.execute("INSERT INTO splits (expense_id, member_id, share) VALUES (?,?,?)", (expense_id, s["member_id"], float(s["share"])))
    conn.commit()
    expense = conn.execute("SELECT * FROM expenses WHERE id=?", (expense_id,)).fetchone()
    splits_rows = conn.execute("SELECT s.*, mem.name as member_name FROM splits s JOIN members mem ON s.member_id=mem.id WHERE s.expense_id=?", (expense_id,)).fetchall()
    result = dict(expense)
    result["splits"] = [dict(s) for s in splits_rows]
    conn.close()
    return jsonify(result), 201

@app.route("/api/groups/<int:gid>/balances", methods=["GET"])
def balances(gid):
    conn = get_db()
    members = conn.execute("SELECT * FROM members WHERE group_id=?", (gid,)).fetchall()
    members = [dict(m) for m in members]
    bal = {m["id"]: 0.0 for m in members}
    expenses = conn.execute("SELECT * FROM expenses WHERE group_id=?", (gid,)).fetchall()
    for e in expenses:
        e = dict(e)
        payer = e["payer_id"]
        splits = conn.execute("SELECT * FROM splits WHERE expense_id=?", (e["id"],)).fetchall()
        for s in splits:
            bal[s["member_id"]] -= float(s["share"])
        bal[payer] += float(e["amount"])
    for m in members:
        m["balance"] = round(bal.get(m["id"],0.0),2)
    conn.close()
    return jsonify(members)

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    root = app.static_folder
    if path and os.path.exists(os.path.join(root, path)):
        return send_from_directory(root, path)
    return send_from_directory(root, "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
