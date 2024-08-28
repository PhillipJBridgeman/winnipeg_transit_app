from dotenv import load_dotenv
import requests
import time
import logging
import os
from dateutil.parser import parse
from colorama import just_fix_windows_console, Fore, Style
from requests.exceptions import RequestException, Timeout, ConnectionError

# Enable colorama for Windows terminals (if needed)
just_fix_windows_console()

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise ValueError("API key not found. Please set the API_KEY in your .env file.")

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RETRY_COUNT = 3
RETRY_DELAY = 5

def fetch_data_with_retries(url):
    """Fetch data from the given URL with retries on failure."""
    logging.info(f"Fetching data from {url}")
    for attempt in range(RETRY_COUNT):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            logging.info("Data fetched successfully.")
            return response
        except (Timeout, ConnectionError) as e:
            logging.error(f"Network error: {e}. Retrying {attempt + 1}/{RETRY_COUNT}...")
            print(f"Network error: {e}. Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
        except RequestException as e:
            logging.error(f"Request failed with status code {response.status_code}: {e}")
            print(f"Error: {response.status_code} - {response.reason}")
            break

    logging.error(f"Failed to fetch data after {RETRY_COUNT} attempts.")
    return None

def user_input():
    """Prompt user for longitude, latitude, and distance, with validation."""
    while True:
        try:
            lon = float(input("Enter the longitude: "))
            lat = float(input("Enter the latitude: "))
            distance = int(input("Enter the distance (in meters): "))

            if not (-180 <= lon <= 180):
                raise ValueError("Longitude must be between -180 and 180.")
            if not (-90 <= lat <= 90):
                raise ValueError("Latitude must be between -90 and 90.")
            if distance <= 0:
                raise ValueError("Distance must be a positive number.")

            logging.info(f"User input received: lon={lon}, lat={lat}, distance={distance}")
            return lon, lat, distance

        except ValueError as e:
            logging.warning(f"Invalid input: {e}")
            print(f"Invalid input: {e}. Please try again.")

def get_bus_stops(lon, lat, distance, api_key):
    """Fetch bus stops based on longitude, latitude, and distance."""
    url_stops = f"https://api.winnipegtransit.com/v3/stops.json?lon={lon}&lat={lat}&distance={distance}&api-key={api_key}"
    return fetch_data_with_retries(url_stops)

def parse_bus_stops(response):
    """Parse bus stops from the API response."""
    try:
        resp_stops = response.json()
        logging.info("Bus stops parsed successfully.")
        return resp_stops.get('stops', [])
    except requests.exceptions.JSONDecodeError as e:
        logging.error(f"Failed to parse bus stops response: {e}")
        print("Failed to parse the response as JSON.")
        return []

def select_bus_stop(stops):
    """Let the user select a bus stop from the list."""
    if not stops:
        logging.info("No bus stops found.")
        print("No bus stops found in the specified radius.")
        return None

    print("Available bus stops:")
    for i, stop in enumerate(stops):
        print(f"{i + 1}: {stop['name']} (ID: {stop['key']})")

    try:
        choice = int(input("Select a bus stop by number: ")) - 1
        if 0 <= choice < len(stops):
            logging.info(f"Bus stop selected: {stops[choice]}")
            return stops[choice]
        else:
            raise ValueError("Selection out of range.")
    except (ValueError, IndexError) as e:
        logging.warning(f"Invalid selection: {e}")
        print("Invalid selection.")
        return None

def fetch_and_parse_schedule(stop_id, api_key):
    """Fetch and parse the bus schedule for a selected stop."""
    url_schedule = f"https://api.winnipegtransit.com/v3/stops/{stop_id}/schedule.json?api-key={api_key}"
    response_schedule = fetch_data_with_retries(url_schedule)

    if response_schedule:
        try:
            schedules = response_schedule.json().get('stop-schedule', {}).get('route-schedules', [])
            logging.info(f"Schedule fetched and parsed successfully for stop ID: {stop_id}")
            return schedules
        except requests.exceptions.JSONDecodeError as e:
            logging.error(f"Failed to parse the schedule response: {e}")
            print("Failed to parse the schedule response as JSON.")
            return []
    else:
        logging.error(f"Failed to fetch schedule for stop ID: {stop_id}")
        return []

def display_schedule(stop_name, schedules):
    """Display the bus schedule for the selected stop."""
    print(f"Bus schedules for {stop_name}:")
    for route in schedules:
        for schedule in route['scheduled-stops']:
            try:
                scheduled_time = parse(schedule['times']['arrival']['scheduled'])
                estimated_time = parse(schedule['times']['arrival']['estimated'])

                if estimated_time > scheduled_time:
                    color = Fore.RED  # Late
                elif estimated_time < scheduled_time:
                    color = Fore.BLUE  # Early
                else:
                    color = Fore.GREEN  # On time

                print(
                    color
                    + f"Route: {route['route']['number']} | Scheduled: {scheduled_time.strftime('%H:%M:%S')} | Estimated: {estimated_time.strftime('%H:%M:%S')}"
                )
            except KeyError as e:
                logging.error(f"Missing expected data in schedule: {e}")
                print("Unexpected data format in schedule.")
            finally:
                print(Style.RESET_ALL)

# Main Program Flow
def main():
    logging.info("Program started.")
    lon, lat, distance = user_input()

    response = get_bus_stops(lon, lat, distance, API_KEY)
    if not response:
        print("Failed to fetch bus stops.")
        return

    stops = parse_bus_stops(response)
    if not stops:
        print("No bus stops found in the specified radius.")
        return

    selected_stop = select_bus_stop(stops)
    if not selected_stop:
        print("No valid bus stop selected.")
        return

    schedules = fetch_and_parse_schedule(selected_stop['key'], API_KEY)
    if not schedules:
        print("Failed to fetch the bus schedule.")
        return

    display_schedule(selected_stop['name'], schedules)
    logging.info("Program completed successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Unexpected error: {e}", exc_info=True)
        print("An unexpected error occurred. Please check the log for details.")