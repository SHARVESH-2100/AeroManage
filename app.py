import os

import mysql.connector
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "aeromanage-dev-key")


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "aero"),
    )


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["user"] = request.form.get("username")
        return redirect(url_for("dashboard"))
    return render_template("login.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM fleet")
    total_fleet = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM missions")
    total_missions = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS count FROM fleet WHERE status='Available'")
    available = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) AS count FROM fleet WHERE status='Busy'")
    busy = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) AS count FROM missions WHERE status='Completed'")
    completed = cursor.fetchone()["count"]

    cursor.execute("SELECT SUM(fuel_capacity) AS total FROM fleet")
    fuel = cursor.fetchone()["total"] or 0

    cursor.execute("SELECT COUNT(*) AS total FROM pilots")
    total_pilots = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM pilots WHERE status='On Mission'")
    active_pilots = cursor.fetchone()["total"]

    conn.close()

    return render_template("dashboard.html",
                           total_fleet=total_fleet,
                           total_missions=total_missions,
                           available=available,
                           busy=busy,
                           completed=completed,
                           fuel=fuel,
                           total_pilots=total_pilots,
                           active_pilots=active_pilots)


# ---------------- FLEET ----------------
@app.route("/fleet", methods=["GET", "POST"])
def fleet():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        cursor.execute("""
            INSERT INTO fleet (aircraft_name, range_km, fuel_capacity, status)
            VALUES (%s,%s,%s,'Available')
        """, (
            request.form["name"],
            request.form["range"],
            request.form["fuel"]
        ))
        conn.commit()
        return redirect(url_for("fleet"))

    cursor.execute("SELECT * FROM fleet")
    fleet_data = cursor.fetchall()
    conn.close()

    return render_template("fleet.html", fleet=fleet_data)


@app.route("/delete_aircraft/<int:aircraft_id>")
def delete_aircraft(aircraft_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fleet WHERE aircraft_id=%s", (aircraft_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("fleet"))


# ---------------- MISSIONS ----------------
@app.route("/mission", methods=["GET", "POST"])
def mission():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        name = request.form["mission_name"]
        distance = int(request.form["distance"])
        aircraft_id = request.form["aircraft_id"]
        pilot_id = request.form["pilot_id"]

        cursor.execute("""
            INSERT INTO missions
            (mission_name, distance_km, aircraft_id, pilot_id, status)
            VALUES (%s,%s,%s,%s,'Planned')
        """, (name, distance, aircraft_id, pilot_id))

        cursor.execute("UPDATE fleet SET status='Busy' WHERE aircraft_id=%s",
                       (aircraft_id,))
        cursor.execute("UPDATE pilots SET status='On Mission' WHERE pilot_id=%s",
                       (pilot_id,))

        conn.commit()
        return redirect(url_for("mission"))

    cursor.execute("""
        SELECT m.mission_id,
               m.mission_name,
               m.distance_km,
               f.aircraft_name,
               p.pilot_name,
               m.status
        FROM missions m
        LEFT JOIN fleet f ON m.aircraft_id = f.aircraft_id
        LEFT JOIN pilots p ON m.pilot_id = p.pilot_id
    """)
    missions = cursor.fetchall()

    cursor.execute("SELECT aircraft_id, aircraft_name FROM fleet WHERE status='Available'")
    aircraft_list = cursor.fetchall()

    cursor.execute("SELECT pilot_id, pilot_name FROM pilots WHERE status='Available'")
    pilot_list = cursor.fetchall()

    conn.close()

    return render_template("mission.html",
                           missions=missions,
                           aircraft_list=aircraft_list,
                           pilot_list=pilot_list)


@app.route("/complete_mission/<int:mission_id>")
def complete_mission(mission_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT aircraft_id, pilot_id FROM missions WHERE mission_id=%s",
                   (mission_id,))
    mission = cursor.fetchone()

    if mission:
        cursor.execute("UPDATE missions SET status='Completed' WHERE mission_id=%s",
                       (mission_id,))
        if mission["aircraft_id"]:
            cursor.execute("UPDATE fleet SET status='Available' WHERE aircraft_id=%s",
                           (mission["aircraft_id"],))
        if mission["pilot_id"]:
            cursor.execute("UPDATE pilots SET status='Available' WHERE pilot_id=%s",
                           (mission["pilot_id"],))
        conn.commit()

    conn.close()
    return redirect(url_for("mission"))


# ---------------- PILOTS ----------------
@app.route("/pilots", methods=["GET", "POST"])
def pilots():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    search = request.args.get("search")

    # Get fleet for dropdown
    cursor.execute("SELECT aircraft_id, aircraft_name FROM fleet")
    fleet_data = cursor.fetchall()

    if request.method == "POST":
        aircraft_id = request.form.get("aircraft_id") or None

        cursor.execute("""
            INSERT INTO pilots
            (pilot_name, pilot_rank, experience_years, aircraft_id, status)
            VALUES (%s,%s,%s,%s,'Available')
        """, (
            request.form["pilot_name"],
            request.form["pilot_rank"],
            request.form["experience_years"],
            aircraft_id
        ))
        conn.commit()
        return redirect(url_for("pilots"))

    if search:
        cursor.execute("""
            SELECT p.*, f.aircraft_name
            FROM pilots p
            LEFT JOIN fleet f ON p.aircraft_id = f.aircraft_id
            WHERE p.pilot_name LIKE %s
        """, ('%' + search + '%',))
    else:
        cursor.execute("""
            SELECT p.*, f.aircraft_name
            FROM pilots p
            LEFT JOIN fleet f ON p.aircraft_id = f.aircraft_id
        """)

    pilot_data = cursor.fetchall()
    conn.close()

    return render_template("pilots.html",
                           pilots=pilot_data,
                           fleet=fleet_data)


@app.route("/delete_pilot/<int:pilot_id>")
def delete_pilot(pilot_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pilots WHERE pilot_id=%s", (pilot_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("pilots"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)