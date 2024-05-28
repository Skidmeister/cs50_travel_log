import os
import sqlite3

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, url_for, send_from_directory, jsonify

from datetime import datetime
import folium

from helpers import get_w3w, get_city_coordinates, create_postcard, check_image_present, check_w3w_api_key, convert_heif_to_jpeg

import pandas as pd

emojis = {1:'😩',
          2:'😔',
          3:'😐',
          4:'😊',
          5:'😃',
          6:'🤩',
          }

transportation_modes = ["boat", "bus", "car", "plane", "train"]
accomodation_types = ["appartment","aribnb","friend's place", "hotel"]

# Configure the app
app = Flask(__name__)

app.secret_key = 'XXX'

# Define the directory to store uploaded files
UPLOADS = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOADS

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///travel_log.db")

# function to serve an image
@app.route('/static/uploads/<path:filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route("/apology")
def apology(text, error=400):
    """Displays a website with an error"""
    return render_template("apology.html", text=text, error=error)


@app.route("/")
def index():
    trips = db.execute("SELECT id, start_date, end_date, country, city, title FROM trips ORDER BY end_date DESC")
    
    #prepare a dictionary with images where key is trip id and value is the name of the file
    images = [file for file in os.listdir('static/uploads') if file !=".DS_Store"]
    images_dict = {}
    for image in images:
        image_id, image_ext = os.path.splitext(image)
        images_dict[int(image_id)] = image

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
        print(city)
        city_coordinates = get_city_coordinates(df, city)
        # Create the popup HTML
        popup_html = f'<a href="trip/{trip['id']}">{trip["title"]}</a>'
        if city_coordinates:
            folium.Marker(location=city_coordinates, popup=popup_html, tooltip=f"{trip['start_date']}-{trip['end_date']}").add_to(m)


    return render_template("trips.html", trips=trips, map=m._repr_html_())



@app.route("/trip/<int:id>")
def trip(id):
    trip = db.execute("SELECT * FROM trips WHERE id = ?", id)[0]
    entries = db.execute("SELECT * FROM entries WHERE trip_id = ? ORDER BY datetime DESC", id)
    spots = db.execute("SELECT * FROM spots WHERE trip_id = ? ORDER By datetime DESC", id)

    image_name = check_image_present(trip_id=id)

    #map
    # getting to the csv-database to get the basic coordinates of a city 
    city = trip['city'].title()
    city_coordinates = get_city_coordinates(df, city)
    # if city coordinates in database get those for initial zoom on the map
    if city_coordinates:
        m = folium.Map(location=city_coordinates, zoom_start=12)
    # if unavailable get coordinates of the first spot that was added to the spots
    elif spots:
        m = folium.Map(location=[spots[-1]['latitude'], spots[-1]['longitude']], zoom_start=12)
    # if spots are not available either, start with the deafault map of Europe
    else:
        m = folium.Map(location=[52.2297, 21.0122], zoom_start=5)

    # Add markers to the map
    for spot in spots:
        folium.Marker(
            location=[spot['latitude'], spot['longitude']], 
            popup=spot['name'], 
            tooltip=spot['datetime'],
            icon=folium.Icon(color="red")
        ).add_to(m) 

    return render_template("trip.html", trip=trip, entries=entries, image=image_name, spots=spots, map=m._repr_html_(), emojis=emojis)

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
    

@app.route("/edit-trip/<int:id>", methods=["GET", "POST"])
def edit_trip(id):
    countries = df['country'].unique().tolist()
    trip = db.execute("SELECT * FROM trips WHERE id = ?", id)[0]
    if request.method == "POST":
        title = request.form.get("title")
        city = request.form.get("city")
        country = request.form.get("country")
        start_date = datetime.strptime(request.form.get("start_date"), "%Y-%m-%d").date()
        end_date = datetime.strptime(request.form.get("end_date"), "%Y-%m-%d").date()
        transportation_mode = request.form.get("transportation_mode")
        transportation_cost = request.form.get("transportation_cost")
        accomodation_type = request.form.get("accomodation_type")
        accomodation_cost = request.form.get("accomodation_cost")

        # edit database
        db.execute("UPDATE trips SET title = ?, city = ?, country = ?, start_date = ?, end_date = ?, transportation_mode = ?, transportation_cost = ?, accomodation_type = ?, accomodation_cost = ? WHERE id = ?", title, city, country, start_date, end_date, transportation_mode, transportation_cost, accomodation_type, accomodation_cost, id)
        return redirect(url_for('trip', id=trip['id']))
    else:
        return render_template("edit_trip.html", id=trip['id'], trip=trip, countries=countries, accomodation_types=accomodation_types, transportation_modes=transportation_modes)




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
        return render_template("add_entry.html", trip=trip, emojis=emojis)



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
        return render_template("edit_entry.html", id=entry['id'], entry=entry, emojis=emojis)

@app.route("/delete-entry/<int:id>", methods=["GET", "POST"])
def delete_entry(id):
    """deletes entry from the database"""
    entry = db.execute("SELECT * FROM entries WHERE id = ?", id)[0]
    if request.method == "POST":
        if request.form.get("confirm") == 'yes':
            db.execute("DELETE FROM entries WHERE id=?", id)
            flash(f"Successfully deleted entry from {entry['datetime']}.")
        else:
            flash("Deletion cancelled.")
        return redirect(url_for("trip", id=entry['trip_id']))
    
    else:
        return render_template("delete_entry.html", id=id, entry=entry)


@app.route("/delete-trip/<int:id>", methods=["GET", "POST"])
def delete_trip(id):
    """deletes trip from the database"""
    trip = db.execute("SELECT * FROM trips WHERE id = ?", id)[0]
    if request.method == "POST":
        if request.form.get("confirm") == 'yes':
            # deletions in the database
            db.execute("DELETE FROM entries WHERE trip_id=?", trip['id'])
            db.execute("DELETE FROM spots WHERE trip_id=?", trip['id'])
            db.execute("DELETE FROM trips WHERE id = ?", id)
            image_name = check_image_present(trip_id=id)          
            if image_name:
                os.remove(f"static/uploads/{image_name}")
            # feedback for the user
            flash(f"Successfully deleted {trip['title']} trip.")
            return redirect(url_for("trips"))
        
        else:
            flash("Deletion cancelled.")
            return redirect(url_for("trip", id=trip['id']))
    
    else:
        return render_template("delete_trip.html", id=id, trip=trip)
    

@app.route("/history")
def history():
    entries = db.execute("SELECT * FROM entries LEFT JOIN trips ON entries.trip_id = trips.id")
    return render_template("history.html", entries=entries, emojis=emojis)




@app.route("/upload-image/<int:trip_id>", methods=["GET", "POST"])
def upload_image(trip_id):
    trip = db.execute("SELECT * FROM trips WHERE id = ?", trip_id)[0]
    if request.method == "POST":
        file = request.files["file"]
        if file:
            #change name but preserve file extension
            file.filename = f"{trip_id}.{file.filename.split('.')[-1]}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
            convert_heif_to_jpeg(f"static/uploads/{file.filename}", trip_id=trip_id)
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
        country = w3w_dict['country']
        nearest_place = w3w_dict['nearestPlace']
        longitude = w3w_dict['coordinates']['lng']
        latitude = w3w_dict['coordinates']['lat']

        # add information to database
        db.execute("INSERT INTO spots (w3s, datetime, name, description, longitude, latitude, country, nearest_place, trip_id) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", words, time, name, description, longitude, latitude, country, nearest_place, trip_id)

        return redirect(url_for("trip", id=trip_id))

    else:
        return render_template("add_spot.html", trip_id=trip_id, trip=trip)

@app.route("/delete_spot/<int:id>", methods=["GET","POST"])
def delete_spot(id):
    """Page to delete a spot"""
    spot = db.execute("SELECT * FROM spots WHERE id =?", id)[0]
    trip = db.execute("SELECT * FROM trips WHERE id =?", spot['trip_id'])[0]
    if request.method == "POST":
        if request.form.get("confirm") == "yes":
            db.execute("DELETE FROM spots WHERE id=?", spot['id'])
            flash(f"Successfully deleted spot: {spot['name']} from {trip['title']}.")
        else:
            flash("Deletion cancelled.")
        return redirect(url_for("trip", id=spot['trip_id']))
    else:
        return render_template("delete_spot.html", trip=trip, spot=spot)

@app.route("/edit_spot/<int:id>", methods=["GET", "POST"])
def edit_spot(id):
    """Page to edit the created spot"""
    spot = db.execute("SELECT * FROM spots WHERE id=?", id)[0]
    if request.method == "POST":
        words = request.form.get("words")
        dt = request.form.get("datetime")
        name = request.form.get("name")
        description = request.form.get("description")
        w3w_dict = get_w3w(words)
        country = w3w_dict['country']
        nearest_place = w3w_dict['nearestPlace']
        longitude = w3w_dict['coordinates']['lng']
        latitude = w3w_dict['coordinates']['lat']
        # changes in the database
        db.execute("UPDATE spots SET w3s = ?, datetime = ?, name = ?, description = ?, longitude = ?, latitude = ?, country = ?, nearest_place = ? WHERE id = ?", words, dt, name, description, longitude, latitude, country, nearest_place, spot['id'])
        flash("Successfully made changes to the database.")
        return redirect(url_for('trip', id=spot['trip_id']))
    else:
        return render_template("edit_spot.html", spot=spot)

@app.route("/generate-postcard/<int:trip_id>", methods = ["GET", "POST"])
def generate_postcard(trip_id):
    """Generates a pdf postcard"""
    trip = db.execute("SELECT * FROM trips WHERE id = ?", trip_id)[0]
    if check_image_present(trip_id=trip_id):
        if request.method == "POST":
            recipient = request.form.get("recipient")
            message = request.form.get("message")
            sender = request.form.get("sender")
            greeting = request.form.get("greeting")
            regards = request.form.get("regards")
            signature = request.form.get("signature")


            create_postcard(recipient, sender, greeting, message, regards, signature, trip)
            flash('The postcard has been successfully generated and can be found in the "postcards" folder.')
            return redirect(url_for("trip", id=trip['id']))
        
        else:
            return render_template("generate_postcard.html", trip_id = trip['id'], trip=trip)
    else:
        return apology("Unfortunately it is impossible to generate postcard without an image. Upload image to this trip first.")
    

# run app.py when the file is run
if __name__ == "__main__":
    if not os.path.exists("travel_log.db"):
        db = sqlite3.connect('travel_log.db')
    
    df = pd.read_csv('worldcities.csv')
    
    check_w3w_api_key()

    # add if clause about the what3words api
    app.run(debug = False)

