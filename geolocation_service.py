import requests

class GeolocationService:
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = "http://api.ipstack.com/{}?access_key={}"

    def get_geolocation(self, ip_address):
        try:
            response = requests.get(self.api_url.format(ip_address, self.api_key))
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error fetching geolocation for {ip_address}: {response.status_code}")
                return None
        except Exception as e:
            print(f"Failed to get geolocation for {ip_address}: {e}")
            return None
