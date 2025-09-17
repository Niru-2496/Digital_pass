from flask import Flask, render_template, request, redirect, session
import sqlite3, hashlib

app = Flask(__name__)
app.secret_key = "your_secret_key"   # needed for sessions

    # ---------------- LOGIN ----------------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = hash_password(request.form["password"])

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        # Check Visitor
        cur.execute("SELECT * FROM visitors WHERE email=? AND password=?",(email,password))
        visitor = cur.fetchone()
        if visitor:
            session["visitor_id"] = visitor[0]
            return redirect("/visitor_dashboard")

        # Check Officer
        cur.execute("SELECT * FROM officers WHERE email=? AND password=?",(email,password))
        officer = cur.fetchone()
        if officer:
            session["officer_id"] = officer[0]
            return redirect("/officer_dashboard")

        # Check Admin
        cur.execute("SELECT * FROM admins WHERE email=? AND password=?",(email,password))
        admin = cur.fetchone()
        if admin:
            session["admin_id"] = admin[0]
            return redirect("/admin_dashboard")

        # Check Agency
        cur.execute("SELECT * FROM agencies WHERE email=? AND password=?",(email,password))
        agency = cur.fetchone()
        if agency:
            session["agency_id"] = agency[0]
            return redirect("/agency_dashboard")

        conn.close()
        return "Invalid login!"
    return render_template("login.html")


# -------------------- Visitor Dashboard --------------------
@app.route("/visitor_dashboard", methods=["GET", "POST"])
def visitor_dashboard():
    if "visitor_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Submit new pass request
    if request.method == "POST":
        type = request.form["type"]
        location = request.form["location"]
        purpose = request.form["purpose"]
        cur.execute("INSERT INTO pass_requests (visitor_id,type,location,purpose) VALUES (?,?,?,?)",
                    (session["visitor_id"], type, location, purpose))
        conn.commit()

    # Show all requests of this visitor
    cur.execute("SELECT * FROM pass_requests WHERE visitor_id=?", (session["visitor_id"],))
    requests = cur.fetchall()
    conn.close()
    return render_template("visitor_dashboard.html", requests=requests)


# -------------------- Officer Dashboard --------------------
@app.route("/officer_dashboard")
def officer_dashboard():
    if "officer_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""SELECT pr.request_id, v.name, pr.type, pr.location, pr.purpose, pr.status
                   FROM pass_requests pr
                   JOIN visitors v ON pr.visitor_id=v.visitor_id
                   WHERE pr.status='pending'""")
    requests = cur.fetchall()
    conn.close()
    return render_template("officer_dashboard.html", requests=requests)


# Officer updates request status
@app.route("/update_request/<int:request_id>/<string:action>")
def update_request(request_id, action):
    if "officer_id" not in session:
        return redirect("/login")

    status = "approved" if action == "approve" else "rejected"
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("UPDATE pass_requests SET status=? WHERE request_id=?", (status, request_id))
    conn.commit()
    conn.close()
    return redirect("/officer_dashboard")


import sqlite3

def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # ---------------- Visitors (from Part 1) ----------------
    cur.execute('''CREATE TABLE IF NOT EXISTS visitors (
        visitor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        phone TEXT,
        password TEXT
    )''')

    # ---------------- Officers (from Part 1) ----------------
    cur.execute('''CREATE TABLE IF NOT EXISTS officers (
        officer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )''')

    # ---------------- Pass Requests (from Part 1) ----------------
    cur.execute('''CREATE TABLE IF NOT EXISTS pass_requests (
        request_id INTEGER PRIMARY KEY AUTOINCREMENT,
        visitor_id INTEGER,
        type TEXT,
        location TEXT,
        purpose TEXT,
        status TEXT DEFAULT 'pending',
        FOREIGN KEY(visitor_id) REFERENCES visitors(visitor_id)
    )''')

    # ---------------- Admins (NEW for Part 2) ----------------
    cur.execute('''CREATE TABLE IF NOT EXISTS admins (
        admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )''')

    # ---------------- Agencies (NEW for Part 2) ----------------
    cur.execute('''CREATE TABLE IF NOT EXISTS agencies (
        agency_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )''')

    # ---------------- Employees under Agencies (NEW for Part 2) ----------------
    cur.execute('''CREATE TABLE IF NOT EXISTS employees (
        emp_id INTEGER PRIMARY KEY AUTOINCREMENT,
        agency_id INTEGER,
        name TEXT,
        department TEXT,
        email TEXT,
        FOREIGN KEY(agency_id) REFERENCES agencies(agency_id)
    )''')

    # ---------------- Pass Types (NEW for Part 2) ----------------
    cur.execute('''CREATE TABLE IF NOT EXISTS pass_types (
        pass_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_name TEXT,
        description TEXT
    )''')



@app.route("/admin_dashboard")
def admin_dashboard():
    if "admin_id" not in session:
        return redirect("/login")
    return "Welcome Admin! (Manage users and pass types here)"

@app.route("/agency_dashboard")
def agency_dashboard():
    if "agency_id" not in session:
        return redirect("/login")
    return "Welcome Agency! (Manage employees and request passes here)"


    # ---------------- Add Officer ----------------
    if request.method == "POST" and "officer_email" in request.form:
        name = request.form["officer_name"]
        email = request.form["officer_email"]
        password = hash_password(request.form["officer_password"])
        try:
            cur.execute("INSERT INTO officers (name,email,password) VALUES (?,?,?)",
                        (name, email, password))
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Officer already exists


             # ---------------- Add Pass Type ----------------
    if request.method == "POST" and "pass_type_name" in request.form:
        type_name = request.form["pass_type_name"]
        description = request.form["pass_type_description"]
        try:
            cur.execute("INSERT INTO pass_types (type_name,description) VALUES (?,?)",
                        (type_name, description))
            conn.commit()
        except sqlite3.IntegrityError:
            pass

    # Fetch data to display
    cur.execute("SELECT * FROM officers")
    officers = cur.fetchall()

    cur.execute("SELECT * FROM pass_types")
    pass_types = cur.fetchall()

    conn.close()
    return render_template("admin_dashboard.html", officers=officers, pass_types=pass_types)


    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("✅ Database updated with Admin, Agency, Employee, and PassType tables")


app.run(debug=True)