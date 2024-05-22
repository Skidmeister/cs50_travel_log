import os
import sqlite3

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, send_from_directory, jsonify

from datetime import datetime
import folium

from helpers import get_w3w, get_city_coordinates, create_postcard

import pandas as pd


# Configure the app
app = Flask(__name__)

# Define the directory to store uploaded files
UPLOADS = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOADS

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///travel_log.db")

# function to serve an image
@app.route('/static/uploads/<path:filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)




@app.route("/")
def index():
    trips = db.execute("SELECT id, start_date, end_date, country, city, title FROM trips ORDER BY end_date DESC")
    
    #prepare a dictionary with images where key is trip id and value is the name of the file
    images = [file for file in os.listdir('static/uploads') if file !=".DS_Store"]
    print(images)
    images_dict = {}
    for image in images:
        image_id, image_ext = os.path.splitext(image)
        images_dict[int(image_id)] = image
    print(images_dict)

    return render_template("index.html", trips=trips, images=images_dict)



@app.route("/trips")
def trips():
    trips = db.execute("SELECT * FROM trips ORDER BY end_date DESC")

    # the map
    # Create a Folium map centered at a Warsaw-heart of Europe location
    m = folium.Map(location=[52.2297, 21.0122], zoom_start=5)
    # Add markers to the map of done trips
    for trip in trips:
        city = trip['city'].title()
        city_coordinates = get_city_coordinates(df, city)
        if city_coordinates:
            folium.Marker(location=city_coordinates, popup=trip['title'], tooltip=f"{trip['start_date']}-{trip['end_date']}").add_to(m)


    return render_template("trips.html", trips=trips, map=m._repr_html_())



@app.route("/trip/<int:id>")
def trip(id):
    trip = db.execute("SELECT * FROM trips WHERE id = ?", id)[0]
    entries = db.execute("SELECT * FROM entries WHERE trip_id = ? ORDER BY datetime DESC", id)
    spots = db.execute("SELECT * FROM spots WHERE trip_id = ? ORDER By datetime DESC", id)

    image_name = None
    # IMAGE: check if the image is there
    for file in os.listdir('static/uploads'):
        file_id, file_ext = os.path.splitext(file)

        if file_id == str(id):
            image_name = file

    #map
    # getting to the csv-database to get the basic coordinates of a city 
    city = trip['city'].title()
    print(city)
    city_coordinates = get_city_coordinates(df, city)
    print(city_coordinates)
    m = folium.Map(location=city_coordinates, zoom_start=12)

    # Add markers to the map
    for spot in spots:
        folium.Marker(
            location=[spot['latitude'], spot['longitude']], 
            popup=spot['name'], 
            tooltip=spot['datetime'],
            icon=folium.Icon(color="red")
        ).add_to(m) 

    return render_template("trip.html", trip=trip, entries=entries, image=image_name, spots=spots, map=m._repr_html_())

@app.route("/get-cities")
def get_cities():
    """Fetches cities based on the selected country and returns  list of cities as a JSON response"""
    country = request.args.get('country')
    cities = df[df['country'] == country]['city'].tolist()
    return cities

@app.route("/add-trip", methods=['GET', 'POST'])
def add_trip():
    # get the list of unique countries for html select box
    countries = df['country'].unique().tolist()

    if request.method == "POST":
        title = request.form.get("title")
        country = request.form.get("country")
        city = request.form.get("city")
        start_date = datetime.strptime(request.form.get("start_date"), "%Y-%m-%d").date()
        end_date = datetime.strptime(request.form.get("end_date"), "%Y-%m-%d").date()


        #add to database
        id = db.execute("INSERT INTO trips (start_date, end_date, country, city, title) VALUES(?, ?, ?, ?, ?)", start_date, end_date, country, city, title)
        return redirect("trips")
    
    else:
        return render_template("add_trip.html", countries = countries)
    

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




@app.route("/upload-image/<int:trip_id>", methods=["GET", "POST"])
def upload_image(trip_id):
    trip = db.execute("SELECT * FROM trips WHERE id = ?", trip_id)[0]
    if request.method == "POST":
        file = request.files["file"]
        if file:
            #change name but preserve file extension
            file.filename = f"{trip_id}.{file.filename.split('.')[-1]}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
            return redirect(url_for("trip", id=trip_id))
        else:
            print("mistake")
    else:
        return render_template("upload_image.html", trip_id=trip_id, trip=trip)


@app.route("/add-spot/<int:trip_id>", methods=["GET", "POST"])
def add_spot(trip_id):
    trip = db.execute("SELECT * FROM trips WHERE id = ?", trip_id)[0]
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        time = request.form.get("datetime")
        words = request.form.get("words")
        w3w_dict = get_w3w(words)
        print(w3w_dict)
        country = w3w_dict['country']
        nearest_place = w3w_dict['nearestPlace']
        longitude = w3w_dict['coordinates']['lng']
        latitude = w3w_dict['coordinates']['lat']

        # add information to database
        db.execute("INSERT INTO spots (w3s, datetime, name, description, longitude, latitude, country, nearest_place, trip_id) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", words, time, name, description, longitude, latitude, country, nearest_place, trip_id)

        return redirect(url_for("trip", id=trip_id))

    else:
        return render_template("add_spot.html", trip_id=trip_id, trip=trip)


@app.route("/generate-postcard/<int:trip_id>", methods = ["GET", "POST"])
def generate_postcard(trip_id):
    """Generates a pdf postcard"""
    trip = db.execute("SELECT * FROM trips WHERE id = ?", trip_id)[0]
    if request.method == "POST":
        recipient = request.form.get("recipient")
        message = request.form.get("message")
        sender = request.form.get("sender")
        greeting = request.form.get("greeting")
        regards = request.form.get("regards")
        signature = request.form.get("signature")


        create_postcard(recipient, sender, greeting, message, regards, signature, trip)

        return redirect(url_for("trip", id=trip['id']))
    
    else:
        return render_template("generate_postcard.html", trip_id = trip['id'], trip=trip)




# run app.py when the file is run
if __name__ == "__main__":
    if not os.path.exists("travel_log.db"):
        db = sqlite3.connect('travel_log.db')
    
    df = pd.read_csv('worldcities.csv')
    
    # add if clause about the what3words api
    app.run(debug = True)