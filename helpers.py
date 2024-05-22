import what3words

# passing the w3w API-key
geocoder = what3words.Geocoder("XT250P1Q")

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

