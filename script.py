from dotenv import load_dotenv
import requests
import time
import logging
import os
from dateutil.parser import parse
from colorama import just_fix_windows_console, Fore, Style
from requests.exceptions import RequestException

# Enable colorama for Windows terminals (if needed)
just_fix_windows_console()

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv('API_KEY')

if not API_KEY:
    raise ValueError("API key not found. Please set the API_KEY in your .env file.")    

# Add logging configuration
logging.basicConfig(filename='app.log', level=logging.ERROR)

RETRY_COUNT = 3
RETRY_DELAY = 5

def fetch_data_with_retries(url):
    for attempt in range(RETRY_COUNT):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response
            elif response.status_code >= 500:
                print(f"Server error (status code: {response.status_code}). Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                break
        except RequestException as e:
            logging.error(f"Request failed: {e}")
            print(f"Request failed. Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
    
    print(f"Failed to fetch data after {RETRY_COUNT} attempts.")
    return None

# lat = 49.89993520529674, lon = -97.14145333888158
# User inputs for longitude, latitude, and search radius
lon = input("Enter the longitude: ")
lat = input("Enter the latitude: ")
distance = input("Enter the distance (in meters): ")

# Fetch nearby bus stops
url_stops = f"https://api.winnipegtransit.com/v3/stops.json?lon={lon}&lat={lat}&distance={distance}&api-key={API_KEY}"
response = fetch_data_with_retries(url_stops)

# Check if the request was successful
if response:
    try:
        resp_stops = response.json()
    except requests.exceptions.JSONDecodeError:
        print("Failed to parse the response as JSON.")
        exit()

    # Display available bus stops
    stops = resp_stops.get('stops', [])
    if not stops:
        print("No bus stops found in the specified radius.")
        exit()

    print("Available bus stops:")
    for i, stop in enumerate(stops):
        print(f"{i+1}: {stop['name']} (ID: {stop['key']})")

    # Ask the user to choose a bus stop
    choice = int(input("Select a bus stop by number: ")) - 1
    if choice < 0 or choice >= len(stops):
        print("Invalid selection.")
        exit()

    selected_stop = stops[choice]
    stop_id = selected_stop['key']

    # Fetch bus schedules for the selected stop
    url_schedule = f"https://api.winnipegtransit.com/v3/stops/{stop_id}/schedule.json?api-key={API_KEY}"
    response_schedule = fetch_data_with_retries(url_schedule)

    # Check if the request was successful
    if response_schedule:
        try:
            resp_schedule = response_schedule.json()
        except requests.exceptions.JSONDecodeError:
            print("Failed to parse the schedule response as JSON.")
            exit()

        # Display arrival times
        schedules = resp_schedule['stop-schedule']['route-schedules']
        print(f"Bus schedules for {selected_stop['name']}:")

        for route in schedules:
            for schedule in route['scheduled-stops']:
                scheduled_time = parse(schedule['times']['arrival']['scheduled'])
                estimated_time = parse(schedule['times']['arrival']['estimated'])

                # Determine the color based on the comparison
                if estimated_time > scheduled_time:
                    color = Fore.RED  # Late
                elif estimated_time < scheduled_time:
                    color = Fore.BLUE  # Early
                else:
                    color = Fore.GREEN  # On time

                print(color + f"Route: {route['route']['number']} | Scheduled: {scheduled_time.strftime('%H:%M:%S')} | Estimated: {estimated_time.strftime('%H:%M:%S')}")
                print(Style.RESET_ALL)
    else:
        print(f"Failed to fetch the bus schedule.")
else:
    print(f"Failed to fetch bus stops.")
