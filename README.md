# TRAVEL-LOG
#### Video Demo:  

https://youtu.be/WN5u2nJ4RBg

#### Description:

Have you ever been asked if you've visited a certain place but couldn't remember when exactly? Or perhaps you have a favorite Italian restaurant in Rome but forgot to jot down its name? If such or similar situations happen to you, Travel-log might be just what you need.

Travel-log is an offline Flask application that uses a browser as its front-end interface. It is designed to store and edit information about your trips. This text-based app functions like a log or diary, allowing you to keep detailed records and memories of your various journeys.

The key features of the app are album, entries, images, spots and postcard generation.


All data entered by the user or fetched through APIs is stored locally in an SQL database with three tables: trips, entries, and spots. Generated postcards are saved as PDFs in the "postcards" folder, while uploaded images are stored in the "static/uploads" folder.

After installation, to start using the app, you need to add a trip. The trip will then be visible in both the album and on the trips page. While creating the trip, you must provide the trip's title, start and end dates, and select the country and city from dropdown menus. These menus are populated with data from a database provided by SimpleMaps.com, ensuring consistency and enabling map display by checking for longitude and latitude of the entered city.

Once a trip is created, users have several options. They can add additional information about the trip, upload an image, add entries, or add spots. 

Only one image can be uploaded per trip, serving as a quick visual reference when browsing through trips in the album. However, this image can be changed at any time. Using the Pillow library, images with a .HEIC extension (common for iPhone users) are converted to JPEGs, ensuring compatibility across all browsers, not just Safari.

However, Travel-log primarily focuses on text data. Users can add, edit, and delete entries. Each entry is a simple text form where users can include their mood using emojis and select an entry type (either a day entry or a trip summary). Entries from all trips can be viewed on a dedicated entry history page.

Another feature of Travel-log is the ability to add spots. Users can enter a 3-word what3words combination, along with a title, time, and description for each spot. What3words allows for precise location identification using unique word combinations (learn more on https://en.wikipedia.org/wiki/What3words). The SQL database stores the latitude and longitude of each spot by integrating the what3words API to fetch the location.
Although users need to check the what3words combination themselves, this method is more convenient than manually entering numerical coordinates and is preferable for privacy reasons, as it avoids fetching the computer's geolocation—especially useful if logging after the trip. The stored spots are displayed on a map implemented using the Folium Python library. Each trip's map focuses on the city's geolocation from the SimpleMaps.com database. If this information is unavailable, the map will focus on the last entered spot for that trip.

Last but not least, a standout feature is the postcard generator. After entering the necessary information, a PDF postcard is created using the ReportLab library. A nice looking Alex Brush font, designed by Robert Leuschke, was used to write the text to the postcard.

Apart from the pages dedicated to specific trips, there are several overview pages. The album provides a visually appealing way to display all trips with their images. The trips page features a table with basic information about each trip and a map showing the cities visited. Lastly, the entry history page displays all entries in chronological order, regardless of the trip.

### Installation:

Since this is a python app the user has to have the python and required libraries preinstalled to use this app. With python in place and the app repository downloaded it is the most convenient for the user to create a python virtual environment inside of the app repository and install the required libraries with the requirements.txt file.

Here is how to install the app from scratch (on Mac):
1.	Download and install python (at least 3.12.)
2.	Download the travel-log repository from GitHub, feel free to change the name of the repository to the name that you like – this is your own, private travel-log.
3.	Open the terminal and go to the downloaded repository.
4.	Create a python virtual environment inside the repository with this command: python3.12 -m venv .venv_name
5.	Activate the virtual environment with this command: source .venv_name/bin/activate
6.	Install the required packages: pip install -r requirements.txt
7.	Run the app: python3.12 app.py
8.	When running the programme for the first time you will be prompted in the terminal to enter API key for what3words. A free API key can be downloaded from https://accounts.what3words.com/select-plan?referrer=/tutorial/python. 
The key to the API will be stored as a .txt file in the repository.
9.	Use the app in your local port, that is displayed in the terminal.

