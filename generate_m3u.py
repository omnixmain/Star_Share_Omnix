import requests
import os
import sys

# Configuration
BASE_URL = "http://dhoomtv.xyz:80"
USERNAME = "P4B9TB9xR8"
PASSWORD = "humongous2tonight"
API_URL = f"{BASE_URL}/player_api.php"

def get_m3u_header():
    return '#EXTM3U\n'

def fetch_categories(action):
    url = f"{API_URL}?username={USERNAME}&password={PASSWORD}&action={action}"
    print(f"Fetching categories: {action}...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            # Create a dictionary mapping category_id to category_name
            cat_map = {item.get('category_id'): item.get('category_name') for item in data}
            print(f"Loaded {len(cat_map)} categories for {action}")
            return cat_map
    except Exception as e:
        print(f"Failed to fetch categories {action}: {e}")
    return {}

def format_live_entry(stream, cat_map):
    # Live stream format
    try:
        name = stream.get('name', 'Unknown').strip()
        stream_id = str(stream.get('stream_id', '')).strip()
        icon = stream.get('stream_icon', '').strip()
        epg_id = stream.get('epg_channel_id', '').strip()
        cat_id = stream.get('category_id', '')
        group_title = cat_map.get(cat_id, 'Uncategorized').strip()
        
        # Calculate URL (Standard Xtream Codes format: /live/username/password/stream_id.ts)
        url = f"{BASE_URL}/live/{USERNAME}/{PASSWORD}/{stream_id}.ts"
        
        entry = f'#EXTINF:-1 tvg-id="{epg_id}" tvg-name="{name}" tvg-logo="{icon}" group-title="{group_title}",{name}\n{url}\n'
        return entry
    except Exception:
        return ""

def format_vod_entry(stream, cat_map):
    # Movie format
    try:
        name = stream.get('name', 'Unknown').strip()
        stream_id = str(stream.get('stream_id', '')).strip()
        icon = stream.get('stream_icon', '').strip()
        extension = stream.get('container_extension', 'mp4').strip()
        if not extension: extension = 'mp4' # Fallback
        
        cat_id = stream.get('category_id', '')
        group_title = cat_map.get(cat_id, 'Uncategorized').strip()
        
        # Calculate URL for VOD
        url = f"{BASE_URL}/movie/{USERNAME}/{PASSWORD}/{stream_id}.{extension}"
        
        entry = f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{icon}" group-title="{group_title}",{name}\n{url}\n'
        return entry
    except Exception:
        return ""

def format_series_entry(series, cat_map):
    # Series format
    try:
        name = series.get('name', 'Unknown').strip()
        series_id = str(series.get('series_id', '')).strip()
        icon = series.get('cover', '').strip()
        cat_id = series.get('category_id', '')
        group_title = cat_map.get(cat_id, 'Uncategorized').strip()
        
        # Series don't have a single stream URL usually. 
        # We stick to the series metadata path.
        url = f"{BASE_URL}/series/{USERNAME}/{PASSWORD}/{series_id}"
        
        entry = f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{icon}" group-title="{group_title}",{name} (Series - Catalog Only)\n{url}\n'
        return entry
    except Exception:
        return ""

def fetch_and_save(action, filename, mode, cat_map):
    url = f"{API_URL}?username={USERNAME}&password={PASSWORD}&action={action}"
    print(f"Fetching content {action}...")
    
    try:
        response = requests.get(url, timeout=60, stream=True)
        response.raise_for_status()
        data = response.json()
        
        if not isinstance(data, list):
            print(f"Error: Expected list for {action} but got {type(data)}")
            return

        print(f"Processing {len(data)} items for {filename}...")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(get_m3u_header())
            
            for item in data:
                entry = ""
                if mode == "live":
                    entry = format_live_entry(item, cat_map)
                elif mode == "vod":
                    entry = format_vod_entry(item, cat_map)
                elif mode == "series":
                    entry = format_series_entry(item, cat_map)
                
                if entry:
                    f.write(entry)
        
        print(f"Successfully saved {filename}")

    except Exception as e:
        print(f"Failed to fetch or save {action}: {e}")

def main():
    # 1. LIVE TV
    live_cats = fetch_categories("get_live_categories")
    fetch_and_save("get_live_streams", "starshare_live.m3u", "live", live_cats)
    
    # 2. MOVIES
    vod_cats = fetch_categories("get_vod_categories")
    fetch_and_save("get_vod_streams", "starshare_movies.m3u", "vod", vod_cats)
    
    # 3. SERIES
    series_cats = fetch_categories("get_series_categories")
    fetch_and_save("get_series", "starshare_series.m3u", "series", series_cats)

if __name__ == "__main__":
    main()
