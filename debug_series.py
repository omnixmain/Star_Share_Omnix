import requests
import json

BASE_URL = "http://dhoomtv.xyz:80"
USERNAME = "P4B9TB9xR8"
PASSWORD = "humongous2tonight"
API_URL = f"{BASE_URL}/player_api.php"

def get_series_info(series_id):
    url = f"{API_URL}?username={USERNAME}&password={PASSWORD}&action=get_series_info&series_id={series_id}"
    print(f"Fetching {url}")
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(e)

if __name__ == "__main__":
    get_series_info(11) # Omar Series
