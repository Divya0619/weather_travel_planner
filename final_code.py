from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import mysql.connector
from flask import render_template
app = Flask(__name__)  # ✅ Define the Flask app
CORS(app)
API_KEY = "a9b49f91afa3434d90a93038251903"  # Replace with your actual API key

# Connect to MySQL
db = mysql.connector.connect(
    host="mainline.proxy.rlwy.net",
    port=50983,
    user="root",
    password="qyJbPZfbLgqsGdzrrXTABGFPfIxsgwVN",  # Replace with your MySQL password
    database="railway"
)
cursor = db.cursor()
cursor.execute("SHOW TABLES")
for table in cursor.fetchall():
    print(table)

def get_travel_cities():
    """Fetch city names from the database."""
    cursor.execute("SELECT city_name FROM Cities")
    cities = [row[0] for row in cursor.fetchall()]
    return cities

@app.route('/save_weather_bulk', methods=['GET'])
def save_weather_bulk():
    saved_cities = []
    failed_cities = []

    travel_cities = get_travel_cities()  # Fetch from DB

    for city in travel_cities:
        url = f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={city}"
        print(f"Fetching weather for: {city}")  # Debugging
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            print(f"Data received for {city}: {data}")  # Debugging

            try:
                temperature = data["current"]["temp_c"]
                humidity = data["current"]["humidity"]
                condition = data["current"]["condition"]["text"]

                query = """INSERT INTO Weather (location, temperature_avg, humidity, weather_type)
                           VALUES (%s, %s, %s, %s)
                           ON DUPLICATE KEY UPDATE 
                           temperature_avg = VALUES(temperature_avg), 
                           humidity = VALUES(humidity), 
                           weather_type = VALUES(weather_type)"""
                values = (city, temperature, humidity, condition)

                cursor.execute(query, values)
                db.commit()

                saved_cities.append(city)
            except KeyError as e:
                print(f"Error parsing weather data for {city}: {e}")  # Debugging
                failed_cities.append(city)
        else:
            print(f"API request failed for {city}, Status Code: {response.status_code}")  # Debugging
            failed_cities.append(city)

    return jsonify({
        "message": "Weather data saved successfully!",
        "saved_cities": saved_cities,
        "failed_cities": failed_cities
    })


@app.route('/get_cities_by_weather', methods=['GET'])
def get_cities_by_weather():
    user_weather = request.args.get('weather', '').lower()
    if not user_weather:
        return jsonify({"error": "Please provide a weather condition."}), 400

    cursor.execute("SELECT location FROM Weather WHERE weather_type LIKE %s", (f"%{user_weather}%",))
    matching_cities = [row[0] for row in cursor.fetchall()]
    
    return jsonify({
        "weather_condition": user_weather,
        "matching_cities": matching_cities
    })
@app.route('/')
def home():
    return render_template("index.html")
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)  # ✅ Flask app runs here
