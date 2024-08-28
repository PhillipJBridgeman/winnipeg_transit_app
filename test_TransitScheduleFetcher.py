import unittest
from TransitScheduleFetcher import TransitScheduleFetcher

class TestTransitScheduleFetcher(unittest.TestCase):
    
    def test_initialization(self):
        api_key = 'a5kXO9s820vtKmybA8AJ'
        tsf = TransitScheduleFetcher(api_key)
        self.assertEqual(tsf.api_key, api_key)
        self.assertEqual(tsf.retry_count, 3)
        self.assertEqual(tsf.retry_delay, 5)

    def test_fetch_data_with_retries_success(self):
        api_key = 'a5kXO9s820vtKmybA8AJ'
        tsf = TransitScheduleFetcher(api_key)
        url = "https://api.winnipegtransit.com/v3/stops.json?lon=-97.14139783589398&lat=-97.14139783589398&distance=100&api-key=a5kXO9s820vtKmybA8AJ"
        response = tsf.fetch_data_with_retries(url)
        self.assertIsNotNone(response)
    
    def test_fetch_data_with_retries_failure(self):
        api_key = 'a5kXO9s820vtKmybA8AJ'
        tsf = TransitScheduleFetcher(api_key)
        url = "https://api.winnipegtransit.com/v3/stops.json?lon=-97.14139783589398&lat=-97.14139783589398&distance=100&api-key=INVALID_API_KEY"
        response = tsf.fetch_data_with_retries(url)
        self.assertIsNone(response)
    
    def test_get_bus_stops(self):
        api_key = 'a5kXO9s820vtKmybA8AJ'
        tsf = TransitScheduleFetcher(api_key)
        lon = -97.14139783589398
        lat = 49.29578430175781
        distance = 100
        response = tsf.get_bus_stops(lon, lat, distance)
        self.assertIsNotNone(response)

if __name__ == '__main__':
    unittest.main()