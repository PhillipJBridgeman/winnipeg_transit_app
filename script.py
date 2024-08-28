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
from requests.exceptions import RequestException, Timeout

# Initialize colorama for Windows console
just_fix_windows_console()

# Load environment variables
load_dotenv()


class TransitScheduleFetcher:
    """
    A class to fetch bus stops and schedules from the Winnipeg Transit API.
    
    Attributes:
    api_key (str): The API key for the Winnipeg Transit API.
    retry_count (int): The number of times to retry a failed request.
    retry_delay (int): The delay between retries in seconds.
    
    Methods:
    fetch_data_with_retries(url): Fetch data from the given URL with retries on failure.
    user_input(): Prompt user for longitude, latitude, and distance, with validation.
    get_bus_stops(lon, lat, distance): Fetch bus stops based on longitude, latitude, and distance.
    parse_bus_stops(response): Parse bus stops from the API response.
    select_bus_stop(stops): Let the user select a bus stop from the list.
    fetch_and_parse_schedule(stop_id): Fetch and parse the bus schedule for a selected stop.
    display_schedule(stop_name, schedules): Display the bus schedule for the selected stop.
    run(): Main method to run the program.
    """
    
    def __init__(self, api_key, retry_count=3, retry_delay=5):
        self.api_key = api_key
        self.retry_count = retry_count
        self.retry_delay = retry_delay

        # Configure logging
        logging.basicConfig(
            filename='app.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def fetch_data_with_retries(self, url):
        """Fetch data from the given URL with retries on failure."""
        logging.info(f"Fetching data from {url}")
        for attempt in range(self.retry_count):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                logging.info("Data fetched successfully.")
                return response
            except (Timeout, ConnectionError) as e:
                logging.error(
                    f"Network error: {e}. Retrying {attempt + 1}/{self.retry_count}..."
                )
                print(
                    f"Network error: {e}. Retrying in {self.retry_delay} seconds..."
                )
                time.sleep(self.retry_delay)
            except RequestException as e:
                logging.error(
                    f"Request failed with status code {response.status_code}: {e}"
                )
                print(f"Error: {response.status_code} - {response.reason}")
                break

        logging.error(f"Failed to fetch data after {self.retry_count} attempts.")
        return None

    def user_input(self):
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

                logging.info(
                    f"User input received: lon={lon}, lat={lat}, distance={distance}"
                )
                return lon, lat, distance

            except ValueError as e:
                logging.warning(f"Invalid input: {e}")
                print(f"Invalid input: {e}. Please try again.")

    def get_bus_stops(self, lon, lat, distance):
        """Fetch bus stops based on longitude, latitude, and distance."""
        url_stops = (
            f"https://api.winnipegtransit.com/v3/stops.json?"
            f"lon={lon}&lat={lat}&distance={distance}&api-key={self.api_key}"
        )
        return self.fetch_data_with_retries(url_stops)

    def parse_bus_stops(self, response):
        """Parse bus stops from the API response."""
        try:
            resp_stops = response.json()
            logging.info("Bus stops parsed successfully.")
            return resp_stops.get('stops', [])
        except requests.exceptions.JSONDecodeError as e:
            logging.error(f"Failed to parse bus stops response: {e}")
            print("Failed to parse the response as JSON.")
            return []

    def select_bus_stop(self, stops):
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
                logging.info("Bus stop selected: %s", stops[choice])
                return stops[choice]
            else:
                raise ValueError("Selection out of range.")
        except (ValueError, IndexError) as e:
            logging.warning(f"Invalid selection: {e}")
            print("Invalid selection.")
            return None

    def fetch_and_parse_schedule(self, stop_id):
        """Fetch and parse the bus schedule for a selected stop."""
        url_schedule = (
            f"https://api.winnipegtransit.com/v3/stops/{stop_id}/schedule.json"
            f"?api-key={self.api_key}"
        )
        response_schedule = self.fetch_data_with_retries(url_schedule)

        if response_schedule:
            try:
                schedules = (
                    response_schedule.json()
                    .get('stop-schedule', {})
                    .get('route-schedules', [])
                )
                logging.info(
                    f"Schedule fetched and parsed successfully for stop ID: {stop_id}"
                )
                return schedules
            except requests.exceptions.JSONDecodeError as e:
                logging.error(f"Failed to parse the schedule response: {e}")
                print("Failed to parse the schedule response as JSON.")
                return []
        else:
            logging.error(f"Failed to fetch schedule for stop ID: {stop_id}")
            return []

    def display_schedule(self, stop_name, schedules):
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
                        + f"Route: {route['route']['number']} | Scheduled: "
                        f"{scheduled_time.strftime('%H:%M:%S')} | Estimated: "
                        f"{estimated_time.strftime('%H:%M:%S')}"
                    )
                except KeyError as e:
                    logging.error(f"Missing expected data in schedule: {e}")
                    print("Unexpected data format in schedule.")
                finally:
                    print(Style.RESET_ALL)

    def run(self):
        """Main method to run the program."""
        logging.info("Program started.")
        lon, lat, distance = self.user_input()

        response = self.get_bus_stops(lon, lat, distance)
        if not response:
            print("Failed to fetch bus stops.")
            return

        stops = self.parse_bus_stops(response)
        if not stops:
            print("No bus stops found in the specified radius.")
            return

        selected_stop = self.select_bus_stop(stops)
        if not selected_stop:
            print("No valid bus stop selected.")
            return

        schedules = self.fetch_and_parse_schedule(selected_stop['key'])
        if not schedules:
            print("Failed to fetch the bus schedule.")
            return

        self.display_schedule(selected_stop['name'], schedules)
        logging.info("Program completed successfully.")


if __name__ == "__main__":
    api_key = os.getenv('API_KEY')
    if not api_key:
        raise ValueError("API key not found. Please set the API_KEY in your .env file.")
    
    tsf = TransitScheduleFetcher(api_key)
    tsf.run()