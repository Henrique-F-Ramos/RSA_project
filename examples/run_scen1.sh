#!/bin/bash

# Run Car 1
gnome-terminal -- bash -c "python3 car.py 1 highway2.json 100 192.168.98.20; exec bash"

# Run Car 2
gnome-terminal -- bash -c "python3 car.py 2 highway2.json 100 192.168.98.30; exec bash"

# Run Car 3
gnome-terminal -- bash -c "python3 car.py 3 highway2.json 100 192.168.98.40; exec bash"
