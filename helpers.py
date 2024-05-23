import what3words
import os


# passing the w3w API-key
geocoder = what3words.Geocoder("XT250P1Q")


# importing modules for postcard
from reportlab.pdfgen import canvas 
from reportlab.pdfbase.ttfonts import TTFont 
from reportlab.pdfbase import pdfmetrics 
from reportlab.lib import colors 
from reportlab.lib.pagesizes import letter, landscape

from datetime import datetime

from PIL import Image
from pillow_heif import register_heif_opener


def get_w3w(w3w):
    """Fetches coordinates of a place indicated with what3words"""
    coordinates = geocoder.convert_to_coordinates(w3w)
    return coordinates

def get_city_coordinates(df, city):
    """Fetches coordinates of a city from a database"""
    city_row = df[df['city'] == city.title()]
    if not city_row.empty:
        latitude = city_row['lat'].values[0]
        longitude = city_row['lng'].values[0]
        return [latitude, longitude]    
    else:
        return None


def check_image_present(trip_id):
    """check if there is trip image in static/uploads"""
    image_name = None
    for file in os.listdir('static/uploads'):
        file_id, file_ext = os.path.splitext(file)

        if file_id == str(trip_id):
            image_name = file 
    return image_name


def create_postcard(recipient, sender, greeting, message, regards, signature, trip):
    """Creates a pdf postcard"""

    #creating a pdf object
    pdf = canvas.Canvas(f"postcards/{trip['title']}.pdf", pagesize=landscape(letter))

    # setting the title of the document 
    pdf.setTitle(f"Postcard from {trip['title']}")

    # Specify the desired width or height
    desired_width = int(landscape(letter)[0] / 2 - 20)  # Desired width
    desired_height = None  # Keep this None to calculate proportionally
   
    # IMAGE: check if the image is there
    for file in os.listdir('static/uploads'):
        file_id, file_ext = os.path.splitext(file)

        if file_id == str(trip['id']):
            register_heif_opener()
            image = Image.open(f'static/uploads/{file}')
            width, height = image.size

            if desired_width and not desired_height:
            # Calculate height proportionally
                new_width = desired_width
                new_height = int((desired_width / width) * height)
            elif desired_height and not desired_width:
            # Calculate width proportionally
                new_height = desired_height
                new_width = int((desired_height / height) * width)

            resized_image = image.resize((new_width, new_height))
            i = resized_image.convert('RGB')
            break


    # registering an external font in python 
    pdfmetrics.registerFont( 
        TTFont('abc', 'AlexBrush-Regular.ttf') 
    ) 

    # generate a horizontal postcard
    if width <= height:

        pdf.drawInlineImage(i, 10, (letter[0] - new_height) / 2)

        # Draw a vertical line in the center of the page
        center_x = (landscape(letter)[0]) / 2
        pdf.line(center_x, 10, center_x, landscape(letter)[1] - 10)

        # Set font for text
        pdf.setFont('abc', 24)
        
        # Place the date on the top right, adjusted
        pdf.drawRightString(landscape(letter)[0] - 20, landscape(letter)[1] - 40, f"{trip['city']}, {trip['country']} - {str(datetime.now().date())}")
        
        # Place "From:" and "To: text
        pdf.drawString(landscape(letter)[0] /2 + 15, landscape(letter)[1] - 90, f"From:   {sender}")
        pdf.drawString(landscape(letter)[0] /2 + 15 , landscape(letter)[1] - 120, f"To:    {recipient}")

        # Place greeting
        pdf.drawString(landscape(letter)[0] / 2 + 15, landscape(letter)[1] - 200, greeting)

        # placing place below the image
        pdf.setFont('abc', 36) 
        pdf.drawCentredString(landscape(letter)[0] / 4, 20, f"{trip['city']}, {trip['country']}")

        # Wrap the message text to fit within the specified width
        text = pdf.beginText(center_x + 20, landscape(letter)[1] - 250)
        text.setFont("abc", 22)
        message_lines = message.split(" ")
        line = ""
        for word in message_lines:
            if pdf.stringWidth(line + word, 'abc', 22) < (landscape(letter)[0] / 2 - 40):
                line += word + " "
            else:
                text.textLine(line)
                line = word + " "
        if line:  # Make sure to add any remaining text
            text.textLine(line)
    
        pdf.drawText(text)

        # Add regards and signature more to the right
        text2 = pdf.beginText(center_x + 160, 60)
        text2.setFont("abc", 22)
        text2.textLine(regards)
        text2.textLine(signature)
        pdf.drawText(text2)

        # saving the pdf 
        pdf.save()
    
    else:
        return apology("The picture you have provided is not vertical or square. Horizontal picture is not yet supported.")

    