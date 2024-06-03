import json
import paho.mqtt.client as mqtt
import threading
from time import sleep
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  

station_data = {}

def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected with result code " + str(rc))
    client.subscribe("vanetza/out/cam")

def on_message(client, userdata, msg):
    global station_data 
    message = msg.payload.decode('utf-8')
    cam_message = json.loads(message)
    
    station_id = cam_message.get('stationID')
    latitude = cam_message.get('latitude')
    longitude = cam_message.get('longitude')
    speed = cam_message.get('speed')

    if station_id is not None and latitude is not None and longitude is not None:
        station_data[station_id] = {
            'latitude': latitude,
            'longitude': longitude,
            'speed': speed
        }
        print(f"Updated station {station_id} to coordinates: ({latitude}, {longitude}) with speed: {speed}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect("192.168.98.10", 1883, 60)

client.loop_start()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/data', methods=['GET'])
def data():
    print("Serving /data endpoint")  
    return jsonify({'stations': station_data})

@app.route('/truck.png')
def truck_icon():
    return send_from_directory('.', 'truck.png')

def start_flask():
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)


flask_thread = threading.Thread(target=start_flask)
flask_thread.daemon = True
flask_thread.start()


while True:
    sleep(0.1)


# import json
# import csv
# import paho.mqtt.client as mqtt
# import threading
# from time import sleep
# from flask import Flask, jsonify, send_from_directory
# from flask_cors import CORS
# from datetime import datetime

# app = Flask(__name__)
# CORS(app)  

# station_data = {}

# 
# header_written = False

# def on_connect(client, userdata, flags, rc, properties=None):
#     print("Connected with result code " + str(rc))
#     client.subscribe("vanetza/out/cam")

# def on_message(client, userdata, msg):
#     global header_written
#     message = msg.payload.decode('utf-8')
#     cam_message = json.loads(message)
    
#     station_id = cam_message.get('stationID')
#     latitude = cam_message.get('latitude')
#     longitude = cam_message.get('longitude')
#     speed = cam_message.get('speed')
#     timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

#     
#     if station_id is not None and latitude is not None and longitude is not None:
#         station_info = {
#             'timestamp': timestamp,
#             'stationID': station_id,
#             'latitude': latitude,
#             'longitude': longitude,
#             'speed': speed
#         }
#         print(f"Updated station {station_id} to coordinates: ({latitude}, {longitude}) with speed: {speed} at {timestamp}")

#         
#         save_to_csv(station_info)

# def save_to_csv(station_info):
#     global header_written
#     with open('station_data.csv', mode='a', newline='') as csv_file:  
#         fieldnames = ['timestamp', 'stationID', 'latitude', 'longitude', 'speed']
#         writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

#         if not header_written:
#             writer.writeheader()
#             header_written = True

#         writer.writerow(station_info)

# client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
# client.on_connect = on_connect
# client.on_message = on_message
# client.connect("192.168.98.10", 1883, 60)

# client.loop_start()

# @app.route('/')
# def index():
#     return send_from_directory('.', 'index.html')

# @app.route('/data', methods=['GET'])
# def data():
#     print("Serving /data endpoint")  
#     return jsonify({'stations': station_data})

# @app.route('/truck.png')
# def truck_icon():
#     return send_from_directory('.', 'truck.png')

# def start_flask():
#     app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)


# flask_thread = threading.Thread(target=start_flask)
# flask_thread.daemon = True
# flask_thread.start()

# while True:
#     sleep(1)



