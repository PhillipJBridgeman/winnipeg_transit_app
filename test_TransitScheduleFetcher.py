import unittest
from unittest.mock import patch, MagicMock
from requests import Timeout
from TransitScheduleFetcher import TransitScheduleFetcher


class test_TransitScheduleFetcher(unittest.TestCase):

    def setUp(self):
        """Set up a TransitScheduleFetcher instance for use in tests."""
        self.api_key = "test_api_key"
        self.fetcher = TransitScheduleFetcher(self.api_key)

    @patch('requests.get')
    def test_fetch_data_with_retries_success(self, mock_get):
        """Test fetching data successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}
        mock_get.return_value = mock_response

        response = self.fetcher.fetch_data_with_retries("http://example.com")
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)

    @patch('requests.get')
    def test_fetch_data_with_retries_failure(self, mock_get):
        """Test fetching data with failed retries."""
        mock_get.side_effect = Timeout

        response = self.fetcher.fetch_data_with_retries("http://example.com")
        self.assertIsNone(response)

    @patch('builtins.input', side_effect=["-97.1415", "49.8999", "500"])
    def test_user_input_valid(self, mock_input):
        """Test valid user input."""
        lon, lat, distance = self.fetcher.user_input()
        self.assertEqual(lon, -97.1415)
        self.assertEqual(lat, 49.8999)
        self.assertEqual(distance, 500)

    @patch('requests.get')
    def test_get_bus_stops_success(self, mock_get):
        """Test fetching bus stops successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "stops": [{"name": "Stop 1", "key": 1001}, {"name": "Stop 2", "key": 1002}]
        }
        mock_get.return_value = mock_response

        stops = self.fetcher.get_bus_stops(-97.1415, 49.8999, 500)
        self.assertIsInstance(stops, list)
        self.assertEqual(len(stops), 2)
        self.assertEqual(stops[0]["name"], "Stop 1")

    @patch('requests.get')
    def test_get_bus_stops_failure(self, mock_get):
        """Test handling of failed bus stop fetch."""
        mock_get.return_value = None

        stops = self.fetcher.get_bus_stops(-97.1415, 49.8999, 500)
        self.assertIsNone(stops)

    @patch('builtins.input', side_effect=["1"])
    def test_select_bus_stop(self, mock_input):
        """Test selecting a bus stop from a list."""
        stops = [{"name": "Stop 1", "key": 1001}, {"name": "Stop 2", "key": 1002}]
        selected_stop = self.fetcher.select_bus_stop(stops)
        self.assertEqual(selected_stop, stops[0])

    @patch('requests.get')
    def test_fetch_and_parse_schedule_success(self, mock_get):
        """Test fetching and parsing bus schedule successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "stop-schedule": {
                "route-schedules": [{"route": {"number": "21"}}, {"route": {"number": "22"}}]
            }
        }
        mock_get.return_value = mock_response

        schedule = self.fetcher.fetch_and_parse_schedule(1001)
        self.assertIsInstance(schedule, list)
        self.assertEqual(len(schedule), 2)

    @patch('requests.get')
    def test_fetch_and_parse_schedule_failure(self, mock_get):
        """Test handling of failed bus schedule fetch."""
        mock_get.return_value = None

        schedule = self.fetcher.fetch_and_parse_schedule(1001)
        self.assertEqual(schedule, [])

    @patch('builtins.print')
    def test_display_schedule(self, mock_print):
        """Test displaying the bus schedule."""
        stop_name = "Stop 1"
        schedules = [{"route": {"number": "21"}, "scheduled-stops": [{"times": {"arrival": {"scheduled": "10:00:00", "estimated": "10:00:00"}}}]},
                     {"route": {"number": "22"}, "scheduled-stops": [{"times": {"arrival": {"scheduled": "12:00:00", "estimated": "12:00:00"}}}]}]

        self.fetcher.display_schedule(stop_name, schedules)
        mock_print.assert_any_call("Bus schedules for Stop 1:")

    @patch('builtins.input', side_effect=["-97.1415", "49.8999", "500"])
    @patch('TransitScheduleFetcher.TransitScheduleFetcher.get_bus_stops')
    @patch('TransitScheduleFetcher.TransitScheduleFetcher.select_bus_stop')
    @patch('TransitScheduleFetcher.TransitScheduleFetcher.fetch_and_parse_schedule')
    @patch('TransitScheduleFetcher.TransitScheduleFetcher.display_schedule')
    def test_run(self, mock_display_schedule, mock_fetch_and_parse_schedule, mock_select_bus_stop, mock_get_bus_stops, mock_input):
        """Test running the program."""
        mock_get_bus_stops.return_value = [{"name": "Stop 1", "key": 1001}]
        mock_select_bus_stop.return_value = {"name": "Stop 1", "key": 1001}
        mock_fetch_and_parse_schedule.return_value = [{"route": {"number": "21"}}]

        self.fetcher.run()

        mock_get_bus_stops.assert_called_once()
        mock_select_bus_stop.assert_called_once()
        mock_fetch_and_parse_schedule.assert_called_once()
        mock_display_schedule.assert_called_once()


if __name__ == '__main__':
    unittest.main()
