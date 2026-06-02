#user123 123
#admin admin123
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import random

def generate_booking_id():
    return "TKT" + str(random.randint(10000, 99999))

app = Flask(__name__)
app.secret_key = "train_system_secret"

trains = ["Express Train", "Superfast Train", "Local Train"]

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# ---------------- DATABASE INIT ----------------
def init_db():
    conn = sqlite3.connect("bookings.db")
    c = conn.cursor()

    # users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)

    # bookings table
    c.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id TEXT,
        train TEXT,
        seat TEXT,
        name TEXT,
        from_station TEXT,
        to_station TEXT
    )
""")

    conn.commit()
    conn.close()

init_db()


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        #  ADMIN CHECK FIRST
        if username == "admin" and password == "admin123":
            session["user"] = "admin"
            session["role"] = "admin"
            return redirect(url_for("admin"))

        # USER CHECK (DATABASE)
        conn = sqlite3.connect("bookings.db")
        c = conn.cursor()

        c.execute("SELECT password FROM users WHERE username=?", (username,))
        user = c.fetchone()

        conn.close()

        if user and user[0] == password:
            session["user"] = username
            session["role"] = "user"
            return redirect(url_for("home"))

        error = "Invalid username or password"

    return render_template("login.html", error=error)

# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("bookings.db")
        c = conn.cursor()

        try:
            c.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, "user")
            )
            conn.commit()
        except:
            return "User already exists"

        conn.close()

        return redirect(url_for("login"))

    return render_template("signup.html")
# ---------------- HOME ----------------
@app.route("/")
def home():

    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("index.html", trains=trains)


# ---------------- ADMIN ----------------
@app.route("/admin")
def admin():

    if "user" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    conn = sqlite3.connect("bookings.db")
    c = conn.cursor()

    c.execute("SELECT booking_id, train, seat, name FROM bookings")
    data = c.fetchall()

    total_bookings = len(data)
    total_passengers = len(set([r[2] for r in data]))
    total_trains = len(set([r[0] for r in data]))

    conn.close()

    return render_template(
        "admin.html",
        bookings=data,
        total_bookings=total_bookings,
        total_passengers=total_passengers,
        total_trains=total_trains
    )

#-------------PLACE AND DATE--------------

@app.route("/search", methods=["POST"])
def search():

    try:
        from_station = request.form["from"]
        to_station = request.form["to"]
        date = request.form["date"]

        trains = [
            "Express Train",
            "Superfast Train",
            "Local Train"
        ]

        return render_template(
            "results.html",
            from_station=from_station,
            to_station=to_station,
            date=date,
            trains=trains
        )

    except Exception as e:
        return f"Error: {str(e)}"
#------------ TRAIN PAGE ----------------
@app.route("/train/<train_name>")
def train(train_name):

    seats = ["A1", "A2", "A3", "B1", "B2", "B3"]

    conn = sqlite3.connect("bookings.db")
    c = conn.cursor()

    c.execute("SELECT seat, name FROM bookings WHERE train=?", (train_name,))
    rows = c.fetchall()

    booked = {seat: name for seat, name in rows}

    conn.close()

    return render_template(
        "train.html",
        train_name=train_name,
        seats=seats,
        booked=booked
    )


# ---------------- BOOK ----------------
@app.route("/book/<train_name>", methods=["POST"])
def book(train_name):

    seat = request.form.get("seat")
    name = request.form.get("name")
    from_station = request.form.get("from")
    to_station = request.form.get("to")

    conn = sqlite3.connect("bookings.db")
    c = conn.cursor()

    c.execute("SELECT * FROM bookings WHERE train=? AND seat=?", (train_name, seat))
    exists = c.fetchone()

    if exists:
        conn.close()
        return f"{seat} already booked!"

    # generate booking id HERE
    booking_id = "TKT" + str(random.randint(10000, 99999))

    c.execute("""
    INSERT INTO bookings (booking_id, train, seat, name, from_station, to_station)
    VALUES (?, ?, ?, ?, ?, ?)
""", (booking_id, train_name, seat, name, from_station, to_station))

    conn.commit()
    conn.close()

    return redirect(url_for("train", train_name=train_name.replace("-", " ")))

#---------------TICKET PRINT--------------

@app.route("/ticket/<train_name>/<seat>")
def ticket(train_name, seat):

    train_name = train_name.replace("-", " ")

    print("TRAIN:", train_name)
    print("SEAT:", seat)

    conn = sqlite3.connect("bookings.db")
    c = conn.cursor()

    c.execute("""
        SELECT booking_id, name, from_station, to_station
        FROM bookings
        WHERE train=? AND seat=?
    """, (train_name, seat))

    data = c.fetchone()

    print("DEBUG DATA:", data)

    conn.close()

    if not data:
        return f"Ticket not found for {train_name} and {seat}"

    return render_template(
        "ticket.html",
        booking_id=data[0],
        name=data[1],
        train=train_name,
        seat=seat,
        from_station=data[2],
        to_station=data[3]
    )
# ---------------- VIEW ----------------
@app.route("/view/<train_name>")
def view(train_name):

    conn = sqlite3.connect("bookings.db")
    c = conn.cursor()

    c.execute("SELECT seat, name FROM bookings WHERE train=?", (train_name,))
    bookings = c.fetchall()

    conn.close()

    return render_template("view.html", train_name=train_name, bookings=bookings)


@app.route("/test")
def test():
    return "Flask is working"
#--------------ADMIN DELETE------------
# @app.route("/admin_delete/<int:id>")
# def admin_delete(id):

#     if "user" not in session or session["role"] != "admin":
#         return redirect(url_for("login"))

#     conn = sqlite3.connect("bookings.db")
#     c = conn.cursor()

#     c.execute("DELETE FROM bookings WHERE booking_id=?", (id,))

#     conn.commit()
#     conn.close()

#     return redirect(url_for("admin"))
#---------------CANCEL------------------

@app.route("/cancel/<ticket_no>")
def cancel(ticket_no):

    conn = sqlite3.connect("bookings.db")
    c = conn.cursor()

    print("Cancelling:", ticket_no)

    c.execute(
        "DELETE FROM bookings WHERE booking_id=?",
        (ticket_no,)
    )

    conn.commit()

    print("Rows deleted:", c.rowcount)

    conn.close()

    return redirect("/")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

conn = sqlite3.connect("bookings.db")
c = conn.cursor()

c.execute("PRAGMA table_info(bookings)")
print(c.fetchall())

if __name__ == "__main__":
    app.run(debug=True)

