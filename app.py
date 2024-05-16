import os
import sqlite3

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for

from datetime import datetime
# Configure the app
app = Flask(__name__)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///travel_log.db")

@app.route("/")
def index():
    trips = db.execute("SELECT id, start_date, end_date, country, city FROM trips")
    return render_template("index.html", trips=trips)

@app.route("/trips")
def trips():
    trips = db.execute("SELECT * FROM trips")
    return render_template("trips.html", trips=trips)

@app.route("/trip/<int:id>")
def trip(id):
    trip = db.execute("SELECT * FROM trips WHERE id = ?", id)[0]
    entries = db.execute("SELECT * FROM entries WHERE trip_id = ?", id)
    return render_template("trip.html", trip=trip, entries=entries)

@app.route("/add-trip", methods=['GET', 'POST'])
def add_trip():
    if request.method == "POST":
        title = request.form.get("title")
        country = request.form.get("country")
        city = request.form.get("city")
        start_date = datetime.strptime(request.form.get("start_date"), "%Y-%m-%d")
        end_date = datetime.strptime(request.form.get("end_date"), "%Y-%m-%d")


        #add to database
        id = db.execute("INSERT INTO trips (start_date, end_date, country, city, title) VALUES(?, ?, ?, ?, ?)", start_date, end_date, country, city, title)
        return redirect("trips")
    
    else:
        return render_template("add_trip.html")
    

@app.route("/add-trip-info/<int:id>", methods=["GET", "POST"])
def add_trip_info(id):
    trip = db.execute("SELECT * FROM trips WHERE id = ?", id)[0]
    if request.method == "POST":
        transportation_mode = request.form.get("transportation_mode")
        transportation_cost = request.form.get("transportation_cost")
        accomodation_type = request.form.get("accomodation_type")
        accomodation_cost = request.form.get("accomodation_cost")

        #add to database
        db.execute("UPDATE trips SET transportation_mode = ?, transportation_cost = ?, accomodation_type = ?, accomodation_cost = ? WHERE id = ?", transportation_mode, transportation_cost, accomodation_type, accomodation_cost, id)
        return redirect(url_for('trip', id=id))
    else:
        return render_template("add_trip_info.html", trip=trip)

@app.route("/add-entry/<int:trip_id>", methods=["GET", "POST"])
def add_entry(trip_id):
    trip = db.execute("SELECT * FROM trips WHERE id=?", trip_id)[0]
    if request.method == 'POST':
        time = datetime.now()
        type = request.form.get("type")
        mood = request.form.get("mood")
        text = request.form.get("text")

        #add to database
        id = db.execute("INSERT INTO entries (trip_id, datetime, type, mood, text) VALUES(?, ?, ?, ?, ?)", trip_id, time, type, mood, text)
        return redirect(url_for("trip", id=trip_id))
    else:
        return render_template("add_entry.html", trip=trip)

@app.route("/edit-entry/<int:id>", methods=["GET", "POST"])
def edit_entry(id):
    entry = db.execute("SELECT * FROM entries WHERE id = ?", id)[0]

    if request.method == "POST":
        time_edited = datetime.now()
        type = request.form.get("type")
        mood = request.form.get("mood")
        text = request.form.get("text")
        
        #edit the database
        db.execute("UPDATE entries SET type = ?, mood = ?, text = ?, last_edit = ? WHERE id = ?", type, mood, text, time_edited, id)
        return redirect(url_for("trip", id=entry['trip_id']))
    else:
        return render_template("edit_entry.html", id=entry['id'], entry=entry)

@app.route("/history")
def history():
    entries = db.execute("SELECT * FROM entries LEFT JOIN trips ON entries.trip_id = trips.id")
    return render_template("history.html", entries=entries)


# run app.py when the file is run
if __name__ == "__main__":
    if not os.path.exists("travel_log.db"):
        db = sqlite3.connect('travel_log.db')
    app.run(debug = True)