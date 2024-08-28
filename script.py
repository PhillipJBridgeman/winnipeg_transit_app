"""
Description: A script that fetches bus stops and schedules from the Winnipeg Transit API.
Author: Phillip Bridgeman
Date: August 26, 2024
Last Modified: August 27, 2024
Version: 1.0.2
Dependencies: requests, python-dotenv, colorama, dateutil
"""

from dotenv import load_dotenv
import requests
import time
import logging
import os
from dateutil.parser import parse
from colorama import just_fix_windows_console, Fore, Style
from requests.exceptions import RequestException, Timeout, ConnectionError

# Initialize colorama for Windows console
just_fix_windows_console()

# Load of environment variables
load_dotenv()

# API key for the Winnipeg Transit API
API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise ValueError("API key not found. Please set the API_KEY in your .env file.")

# Configure Logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Retry Configuration
RETRY_COUNT = 3
RETRY_DELAY = 5

def fetch_data_with_retries(url):
    """
    Fetch data from the given URL with a specified number of retries on failure.

    Args:
        url (str): The URL to fetch data from.

    Returns:
        requests.Response: The response object containing the data if the request is successful.
        None: If all retry attempts fail.

    Raises:
        ValueError: If the URL is not valid.
    
    Example:
        response = fetch_data_with_retries("https://api.example.com/data")
        if response:
            data = response.json()
    """
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
    """
    Prompt the user for longitude, latitude, and distance, ensuring valid input.

    Returns:
        tuple: A tuple containing the longitude (float), latitude (float), and distance (int).
    
    Raises:
        ValueError: If the user inputs invalid longitude, latitude, or distance.

    Example:
        lon, lat, distance = user_input()
    """
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
    """
    Fetch bus stops from the Winnipeg Transit API based on the given coordinates and distance.

    Args:
        lon (float): Longitude for the location.
        lat (float): Latitude for the location.
        distance (int): Radius in meters to search for bus stops.
        api_key (str): API key for authentication.

    Returns:
        requests.Response: The response object containing the bus stops data if the request is successful.
        None: If the request fails after retries.

    Example:
        response = get_bus_stops(-97.1375, 49.8998, 500, "your_api_key")
    """
    url_stops = f"https://api.winnipegtransit.com/v3/stops.json?lon={lon}&lat={lat}&distance={distance}&api-key={api_key}"
    return fetch_data_with_retries(url_stops)

def parse_bus_stops(response):
    """
    Parse the bus stops from the API response.

    Args:
        response (requests.Response): The response object from the API containing bus stops data.

    Returns:
        list: A list of bus stops dictionaries if parsing is successful.
        list: An empty list if parsing fails or no stops are found.

    Example:
        stops = parse_bus_stops(response)
        if stops:
            for stop in stops:
                print(stop['name'])
    """
    try:
        resp_stops = response.json()
        logging.info("Bus stops parsed successfully.")
        return resp_stops.get('stops', [])
    except requests.exceptions.JSONDecodeError as e:
        logging.error(f"Failed to parse bus stops response: {e}")
        print("Failed to parse the response as JSON.")
        return []

def select_bus_stop(stops):
    """
    Allow the user to select a bus stop from the provided list.

    Args:
        stops (list): A list of bus stops to choose from.

    Returns:
        dict: A dictionary representing the selected bus stop.
        None: If no valid selection is made.

    Example:
        selected_stop = select_bus_stop(stops)
        if selected_stop:
            print(selected_stop['name'])
    """
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
    """
    Fetch and parse the bus schedule for the selected stop.

    Args:
        stop_id (str): The unique identifier for the bus stop.
        api_key (str): API key for authentication.

    Returns:
        list: A list of dictionaries containing the schedule for each route.
        list: An empty list if the request fails or parsing is unsuccessful.

    Example:
        schedules = fetch_and_parse_schedule("10064", "your_api_key")
        if schedules:
            for schedule in schedules:
                print(schedule)
    """
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
    """
    Display the bus schedule for the selected stop.

    Args:
        stop_name (str): The name of the selected bus stop.
        schedules (list): A list of dictionaries containing the schedule for each route.

    Example:
        display_schedule("Main & Broadway", schedules)
    """
    print(f"Bus schedules for {stop_name}:")
    for route in schedules:
        for schedule in route['scheduled-stops']:
            try:
                scheduled_time = parse(schedule['times']['arrival']['scheduled'])
                estimated_time = parse(schedule['times']['arrival']['estimated'])

                if estimated_time > scheduled_time:
                    color = Fore.RED # Late
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

def main():
    """
    Main function to execute the script.

    This function orchestrates the input collection, data fetching, and display of bus stop and schedule information.
    """
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