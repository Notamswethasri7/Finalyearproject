from flask import Flask, render_template, request, jsonify
import osmnx as ox
import networkx as nx
import folium
import joblib
import numpy as np
import urllib.request
import urllib.parse
from opencage.geocoder import OpenCageGeocode
app = Flask(__name__)

# Load ML Model
model = joblib.load('litemodel.sav')

# OpenCage API Key (Replace with your key)
API_KEY = "a51b7df648f24977a2f403014782bb4d"
geocoder = OpenCageGeocode(API_KEY)

# Load road network
city = "Bangalore, India"
graph = ox.graph_from_place(city, network_type="drive")

# Assign safety weights
for u, v, data in graph.edges(data=True):
    data["weight"] = data.get("length", 1)  # Default weight is road length
    if "fatalities" in data:
        data["weight"] *= (1 + data["fatalities"] * 0.1)  # Penalize dangerous roads

# 🔹 Function: Get Coordinates from Location Name
def get_coordinates(location_name):
    result = geocoder.geocode(location_name)
    if result:
        return result[0]['geometry']['lat'], result[0]['geometry']['lng']
    return None, None

# 🔹 Function: Send SMS Alerts
def sendSMS(apikey, numbers, sender, message):
    data = urllib.parse.urlencode({'apikey': apikey, 'numbers': numbers, 'message': message, 'sender': sender})
    data = data.encode('utf-8')
    request = urllib.request.Request("https://api.textlocal.in/send/?")
    f = urllib.request.urlopen(request, data)
    return f.read()

# 🔹 Route Calculation API
@app.route('/safe_route', methods=['POST'])
def safe_route():
    data = request.json
    start_name = data.get("start")
    dest_name = data.get("destination")

    start_lat, start_lon = get_coordinates(start_name)
    dest_lat, dest_lon = get_coordinates(dest_name)

    if not start_lat or not dest_lat:
        return jsonify({"error": "Invalid locations"}), 400

    orig = ox.distance.nearest_nodes(graph, start_lon, start_lat)
    dest = ox.distance.nearest_nodes(graph, dest_lon, dest_lat)

    route = nx.shortest_path(graph, orig, dest, weight="weight")
    route_coords = [(graph.nodes[node]["y"], graph.nodes[node]["x"]) for node in route]

    return jsonify({"route": route_coords})
# 🔹 Accident Prediction API
def cal(ip):
    input = dict(ip)
    Did_Police_Officer_Attend = input['Did_Police_Officer_Attend'][0]
    age_of_driver = input['age_of_driver'][0]
    vehicle_type = input['vehicle_type'][0]
    age_of_vehicle = input['age_of_vehicle'][0]
    engine_cc = input['engine_cc'][0]
    day = input['day'][0]
    weather = input['weather'][0]
    light = input['light'][0]
    roadsc = input['roadsc'][0]
    gender = input['gender'][0]
    speedl = input['speedl'][0]
    data = np.array([Did_Police_Officer_Attend, age_of_driver, vehicle_type, age_of_vehicle, engine_cc, day, weather, roadsc, light, gender, speedl])

    print("logging",data)
    data = data.astype(float)
    data = data.reshape(1, -1)

    try: result = model.predict(data)
    except Exception as e: result = str(e)

    return str(result[0])
    
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')
@app.route('/', methods=['POST'])
def get():
    return cal(request.form)
@app.route('/visual/')
def visual():
    return render_template('visual.html')
@app.route('/export1/')
def export1():
    return render_template('export1.html')
@app.route('/saferoute/')
def saferoute():
    return render_template('saferoute.html')
# 🔹 Run Flask App
if __name__== '__main__':
    app.run(host='0.0.0.0', debug=True, port=4000)