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

        
        # creating the title by setting it's font  
        # and putting it on the canvas 
        pdf.setFont('abc', 36) 
        pdf.drawCentredString(450, 10, f"{trip['city']}, {trip['country']}")

        # creating the subtitle by setting it's font,  
        # colour and putting it on the canvas 
        pdf.setFillColorRGB(0, 0, 255) 
        pdf.setFont("abc", 18) 
        pdf.drawCentredString(450, 720, f"From: {sender}")
        pdf.drawCentredString(450, 820, f"To: {recipient}")
        


        words = message.split(" ")
        text_lines = []
        counter = 0
        text_line = "" 
        for word in words:     
            if counter < 4:
                text_line += f"{word} "
                counter += 1
            else:
                text_lines.append(text_line)
                text_line = ""
                counter = 0

        #handle last text line if thera are some words left
        if text_line:
            text_lines.append(text_line)

        # creating a multiline text using  
        # textline and for loop 
        # pdf.drawText(str(datetime.now()))
        
        text = pdf.beginText(450, 680)
        text.setFont("abc", 18)
        text.setFillColor(colors.red)
        text.textLine(str(datetime.now().date()))
        text.textLine(greeting) 
        for line in text_lines: 
            text.textLine(line) 
        text.textLine(regards)
        text.textLine(signature)
        pdf.drawText(text) 

        # drawing a image at the  
        # specified (x.y) position 






    # saving the pdf 
    pdf.save()