import json
import paho.mqtt.client as mqtt
import threading
from time import sleep
import time
import argparse
import math
from geopy.distance import geodesic
from geopy.point import Point
from flask import Flask, render_template, jsonify
import sys

def parse_arguments():
    parser = argparse.ArgumentParser(description='Car script with starting position and route file')
    parser.add_argument('my_id', type=int, help='ID of the car')
    parser.add_argument('json_file', type=str, help='JSON file containing the route')
    parser.add_argument('inicial_speed', type=str, help='Starting speed of every car')
    parser.add_argument('ip', type=str, help='OBU ip ')
    return parser.parse_args()

args = parse_arguments()

my_id = args.my_id
json_file = args.json_file
inicial_speed = float(args.inicial_speed)
n_cars = 3
leader_defined = False
cam_count = 0
following = 0
hard_coded_stop = 0
start_break = 0

security_distance = 40


def load_route(json_file):
    with open(json_file, 'r') as f:
        return json.load(f)

route = load_route(json_file)

if my_id <= len(route):
    start_index = my_id - 1
else:
    start_index = 0  

latitude = route[start_index]['latitude']
longitude = route[start_index]['longitude']
heading = 0
speed_kmh = inicial_speed  
my_speed = speed_kmh / 3.66 


station_ids = {my_id}
station_data = {my_id: (latitude, longitude, heading, my_speed)}
sorted_station_ids = {my_id}
aux = {my_id}

def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected with result code " + str(rc))
    client.subscribe("vanetza/out/cam")
    client.subscribe("vanetza/out/denm")

def on_message(client, userdata, msg):
    global aux, cam_count, leader_defined, station_data, station_ids, sorted_station_ids, route, n_cars
    message = msg.payload.decode('utf-8')
    cam_message = json.loads(message)
    if msg.topic == "vanetza/out/denm":
        if cam_message["fields"]["header"]["messageID"] == 1:
            n_cars = n_cars-1
            reset_order()
            print("Entrou com type 2")
        

    if msg.topic == "vanetza/out/cam":
        #if leader_defined == False:    
            print(f"cam_count: {cam_count}")
            
            station_id = cam_message["stationID"]
            station_lat = cam_message["latitude"]
            station_lon = cam_message["longitude"]
            station_heading = cam_message["heading"]
            station_speed = cam_message["speed"]
            
            
            station_data[station_id] = (station_lat, station_lon, station_heading, station_speed)
            station_ids.add(station_id)
            aux.add(station_id)
             
            
            if len(aux) >= n_cars:
                sorted_station_ids, distances_to_ref = get_ordered_station_ids(station_data, route)
                calculate_distances_between_cars(sorted_station_ids, station_data)
            
            print(station_ids)
            cam_count += 1
            
            if len(aux) == n_cars:
                aux = {my_id}
            if cam_count == 10:
                leader_defined = True 
            if cam_count == 300:
                reset_order()

def reset_order():
    global aux, cam_count, leader_defined, station_data, station_ids, sorted_station_ids, route, n_cars
    print("\nRESETING ORDER ARRAY\n")
    leader_defined = False
    station_ids = {my_id}
    station_data = {my_id: (latitude, longitude, heading, my_speed)}
    sorted_station_ids = {my_id}
    aux = {my_id}
    cam_count = 0

            

def get_ordered_station_ids(station_data, route):
    ref_lat, ref_lon = route[0]['latitude'], route[0]['longitude']
    #print(f"Reference Point: ({ref_lat}, {ref_lon})")
    
    def sort_key(sid):
        lat, lon, _, _ = station_data[sid]  # Unpack four values
        return geodesic((ref_lat, ref_lon), (lat, lon)).meters

    sorted_station_ids = sorted(station_ids, key=sort_key)
    
    distances_to_ref = {sid: geodesic((ref_lat, ref_lon), (station_data[sid][0], station_data[sid][1])).meters for sid in sorted_station_ids}
    
    
    for sid in sorted_station_ids:
        dist_to_ref = distances_to_ref[sid]
        #print(f"Station ID: {sid}, Distance to Reference Point: {dist_to_ref:.2f} meters")
    
    return sorted_station_ids, distances_to_ref

def calculate_distances_between_cars(sorted_station_ids, station_data):
    #print("Distances between cars:")
    for i in range(len(sorted_station_ids)):
        for j in range(i + 1, len(sorted_station_ids)):
            sid1 = sorted_station_ids[i]
            sid2 = sorted_station_ids[j]
            dist_between_cars = geodesic((station_data[sid1][0], station_data[sid1][1]), (station_data[sid2][0], station_data[sid2][1])).meters
            #print(f"Distance between Station ID {sid1} and Station ID {sid2}: {dist_between_cars:.2f} meters")

def send_cam_message(client):
    global latitude, longitude, heading, my_speed, speed_kmh, station_data
    with open('in_cam.json') as f:
        m = json.load(f)
        m["stationID"] = my_id
        m["latitude"] = latitude
        m["longitude"] = longitude
        m["heading"] = heading
        m["speed"] = my_speed
        m = json.dumps(m)
        client.publish("vanetza/in/cam", m)
    
    
    station_data[my_id] = (latitude, longitude, heading, my_speed)
    print(f"Sent CAM: ID={my_id} coord=({latitude},{longitude}), Heading={heading}, Speed={speed_kmh}")

def send_denm_message(client,denm_type):
    with open('in_denm.json') as f:
        m = json.load(f)
        m["stationID"] = my_id
        m["latitude"] = latitude
        m["longitude"] = longitude
        m["heading"] = heading
        m["speed"] = my_speed
        m["messageID"] = denm_type
        m = json.dumps(m)
        client.publish("vanetza/in/denm", m)
    
    print(f"Sent denm: ID={my_id} coord=({latitude},{longitude}), Heading={heading}, Speed={my_speed}, Type={denm_type}")

station_data[my_id] = (latitude, longitude, heading, my_speed)
print(f"Sent CAM: ID={my_id} coord=({latitude},{longitude}), Heading={heading}, Speed={my_speed}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect  
client.on_message = on_message
client.connect(args.ip, 1883, 60)

client.loop_start()

def update_position_and_send_cam():
    global start_index, latitude, longitude, heading, my_speed, speed_kmh, station_data, hard_coded_stop, start_break
    while True:
        if start_index < len(route) - 1:
            next_position = (route[start_index + 1]['latitude'], route[start_index + 1]['longitude'])

            while True:
                print("start_break: ", start_break)
                current_lat, current_lon = latitude, longitude
                next_lat, next_lon = next_position

                heading = calculate_heading(current_lat, current_lon, next_lat, next_lon)
                distance_to_travel = my_speed

                new_lat, new_lon = calculate_new_position(current_lat, current_lon, distance_to_travel, heading)
                latitude, longitude = new_lat, new_lon
                station_data[my_id] = (latitude, longitude, heading, my_speed)

               
                if geodesic((new_lat, new_lon), next_position).meters < my_speed:
                    latitude, longitude = next_position

                    if "break" in route[start_index + 1] and route[start_index + 1]["break"] == my_id:
                        print(f"\n\n\n\n\nReached break point: ({latitude}, {longitude})\n\n\n\n\n")
                        hard_coded_stop = 1

                    if "break_time" in route[start_index + 1]:
                        sleep_time = route[start_index + 1]["break_time"]

                    if "leave" in route[start_index + 1] and route[start_index + 1]["leave"] == my_id:
                        print("\n\nLEAVE\n\n")
                        send_denm_message(client,2)
                        sys.exit()

                    start_index += 1
                    break
            

                send_cam_message(client)
                

                if hard_coded_stop == 1:
                    
                    print(f"Start Break:{start_break} my Speed:{my_speed}")
                    breaking()
                    

                    

    

                    if start_break == 2:
                    
                        print(f"NOW SLEEPING FOR {sleep_time} iterations")
                    
                        sleep(sleep_time)
                        start_break = 0
                        hard_coded_stop = 0
                        print(f"\n\nStart DRIVING\n\n")
                        my_speed = inicial_speed/3.6
                    else:
                        start_break = 1

                    
                sleep(1)
        else:
            speed_kmh = 0
            my_speed = 0
            while True:
                
                send_cam_message(client)
                sleep(1) 

        
        
        
def calculate_new_position(lat1, lon1, distance, bearing):
    start_point = Point(lat1, lon1)
    destination = geodesic(meters=distance).destination(point=start_point, bearing=bearing)
    return destination.latitude, destination.longitude

def calculate_heading(lat1, lon1, lat2, lon2):
    delta_lon = lon2 - lon1
    delta_lat = lat2 - lat1
    angle = math.atan2(delta_lon, delta_lat)
    bearing = (math.degrees(angle) + 360) % 360
    return bearing

def calculate_leader_speed(distance_flag):
    global my_speed
    
    if start_break == 0:
        if distance_flag == 2:
            my_speed = (inicial_speed)/3.66
        elif distance_flag == 1:
            my_speed = (inicial_speed)/3.66
    print(f"Calculating leader speed:{my_speed}")

def get_following_speed(following_id):
    if following_id in station_data:
        return station_data[following_id][3]  
    else:
        return None

def update_speed(dist_between_cars, following_speed):
    global my_speed, inicial_speed, start_break
    if start_break == 0:
        x = ((following_speed) + (20/3.66) * (1 - math.exp(-(dist_between_cars - security_distance) / 10)))
        if x < 0:
            x = 0
        my_speed = x

def breaking():
    global my_speed, start_break
    deceleration = 4  
    new_speed = my_speed - deceleration
    
   
    if new_speed < 0:
        new_speed = 0
        start_break = 2
    
    my_speed = new_speed

position_cam_thread = threading.Thread(target=update_position_and_send_cam)
position_cam_thread.daemon = True
position_cam_thread.start()


while True:
    if leader_defined == True:
        if my_id == sorted_station_ids[-1]:
            print(f"My ID {my_id} is the LEADER")
            my_lat, my_lon = station_data[my_id][0], station_data[my_id][1]
            distances_greater_than_50 = 0 

            for other_id in sorted_station_ids[:-1]:  
                other_lat, other_lon = station_data[other_id][0], station_data[other_id][1]
                dist_between_cars = geodesic((my_lat, my_lon), (other_lat, other_lon)).meters
                print(f"Distance between Station ID {my_id} and Station ID {other_id}: {dist_between_cars:.2f} meters")

                if dist_between_cars > 50:
                    distances_greater_than_50 += 1
            
            
            if distances_greater_than_50 == 0:
                distance_flag = 0
            elif distances_greater_than_50 == 1:
                distance_flag = 1
            else:
                distance_flag = 2
            
            if distance_flag > 0:
                calculate_leader_speed(distance_flag)

        else:
            my_id_position = sorted_station_ids.index(my_id)
            following = sorted_station_ids[my_id_position + 1]
            
            following_speed = get_following_speed(following)
            if following_speed is not None:
                print(f"Following ID {following} with speed {following_speed:.2f} m/s, my speed is {my_speed}")
            else:
                print(f"Could not retrieve speed for following ID {following}")
        
            
            my_lat, my_lon = station_data[my_id][0], station_data[my_id][1]
            following_lat, following_lon = station_data[following][0], station_data[following][1]
            dist_between_cars = geodesic((my_lat, my_lon), (following_lat, following_lon)).meters

            update_speed(dist_between_cars, following_speed)
            print(f"My speed is={my_speed}")

            print(f"Distance between Station ID {my_id} and Station ID {following}: {dist_between_cars:.2f} meters")
    sleep(1)