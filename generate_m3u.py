import requests
import os
import sys
import time
import concurrent.futures

# Configuration
BASE_URL = "http://dhoomtv.xyz:80"
USERNAME = "P4B9TB9xR8"
PASSWORD = "humongous2tonight"
API_URL = f"{BASE_URL}/player_api.php"

def get_m3u_header():
    return '#EXTM3U\n'

def fetch_with_retry(url, retries=3, timeout=120):
    for i in range(retries):
        try:
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status()
            return response.json()
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"Attempt {i+1} failed for {url}: {e}")
            if i < retries - 1:
                time.sleep(5)  # Wait before retry
            else:
                return {} # Return empty dict/list on failure instead of raising to keep partial results working

def fetch_categories(action):
    url = f"{API_URL}?username={USERNAME}&password={PASSWORD}&action={action}"
    print(f"Fetching categories: {action}...")
    try:
        data = fetch_with_retry(url, retries=3, timeout=60)
        if isinstance(data, list):
            cat_map = {item.get('category_id'): item.get('category_name') for item in data}
            print(f"Loaded {len(cat_map)} categories for {action}")
            return cat_map
    except Exception as e:
        print(f"Failed to fetch categories {action}: {e}")
    return {}

def format_live_entry(stream, cat_map):
    try:
        name = str(stream.get('name', '') or 'Unknown').strip()
        stream_id = str(stream.get('stream_id', '')).strip()
        icon = str(stream.get('stream_icon', '') or '').strip()
        epg_id = str(stream.get('epg_channel_id', '') or '').strip()
        
        cat_id = stream.get('category_id')
        group_title = cat_map.get(cat_id)
        if not group_title:
             group_title = cat_map.get(str(cat_id), 'Uncategorized')
        
        group_title = str(group_title or 'Uncategorized').strip()
        url = f"{BASE_URL}/live/{USERNAME}/{PASSWORD}/{stream_id}.ts"
        
        entry = f'#EXTINF:-1 tvg-id="{epg_id}" tvg-name="{name}" tvg-logo="{icon}" group-title="{group_title}",{name}\n{url}\n'
        return entry
    except Exception:
        return ""

def format_vod_entry(stream, cat_map):
    try:
        name = str(stream.get('name', '') or 'Unknown').strip()
        stream_id = str(stream.get('stream_id', '')).strip()
        icon = str(stream.get('stream_icon', '') or '').strip()
        extension = str(stream.get('container_extension', '') or 'mp4').strip()
        if not extension: extension = 'mp4' 
        
        cat_id = stream.get('category_id')
        group_title = cat_map.get(cat_id)
        if not group_title:
             group_title = cat_map.get(str(cat_id), 'Uncategorized')
             
        group_title = str(group_title or 'Uncategorized').strip()
        url = f"{BASE_URL}/movie/{USERNAME}/{PASSWORD}/{stream_id}.{extension}"
        
        entry = f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{icon}" group-title="{group_title}",{name}\n{url}\n'
        return entry
    except Exception:
        return ""

def fetch_series_episodes(series, cat_map):
    """
    Fetches episodes for a single series and returns a string containing all M3U entries for that series.
    """
    try:
        series_id = str(series.get('series_id', '')).strip()
        name = str(series.get('name', '') or 'Unknown').strip()
        icon = str(series.get('cover', '') or '').strip()
        cat_id = series.get('category_id')
        
        group_title = cat_map.get(cat_id)
        if not group_title:
             group_title = cat_map.get(str(cat_id), 'Uncategorized')
        group_title = str(group_title or 'Uncategorized').strip()

        # Fetch detailed info for this series
        info_url = f"{API_URL}?username={USERNAME}&password={PASSWORD}&action=get_series_info&series_id={series_id}"
        data = fetch_with_retry(info_url, retries=2, timeout=60)
        
        if not data or not isinstance(data, dict) or 'episodes' not in data:
            return ""

        episodes_map = data['episodes']
        entries = []
        
        # 'episodes' is a dict keyed by season number (as string or int)
        # We sort seasons to keep order
        
        # Helper to convert keys to int for sorting safely
        def try_int(k):
            try: return int(k)
            except: return 0

        sorted_seasons = sorted(episodes_map.keys(), key=try_int)

        for season_num in sorted_seasons:
            season_episodes = episodes_map[season_num]
            if isinstance(season_episodes, list):
                for ep in season_episodes:
                    # Construct Episode Entry
                    # Format: Show Name - SxxExx - Title (if available)
                    
                    ep_id = str(ep.get('id', ''))
                    ep_container = str(ep.get('container_extension', 'mp4'))
                    ep_season = str(ep.get('season', season_num))
                    ep_num = str(ep.get('episode_num', ''))
                    ep_title = str(ep.get('title', '')).strip()
                    
                    # Ensure minimal valid naming
                    display_title = f"{name} - S{ep_season}E{ep_num}"
                    if ep_title and ep_title != display_title:
                         display_title = ep_title # Use the title provided by API if it's descriptive
                    
                    # Clean display title of newlines
                    display_title = display_title.replace('\n', ' ').replace('\r', '')

                    # Build URL
                    # Standard XC Series URL: /series/user/pass/id.ext
                    video_url = f"{BASE_URL}/series/{USERNAME}/{PASSWORD}/{ep_id}.{ep_container}"
                    
                    entry = f'#EXTINF:-1 tvg-name="{display_title}" tvg-logo="{icon}" group-title="{group_title}",{display_title}\n{video_url}\n'
                    entries.append(entry)
        
        return "".join(entries)

    except Exception as e:
        print(f"Error processing series {series.get('name')}: {e}")
        return ""

def process_series_concurrently(series_list, cat_map, filename, max_workers=10):
    total = len(series_list)
    print(f"Starting parallel fetch for {total} series with {max_workers} workers...")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(get_m3u_header())
        f.write(f"# Total Series Processed: {total}\n")
        f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')} UTC\n")
        
        count = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # map returns iterator strictly in order of input iterable, which works well
            # but we might want as_completed to write faster?
            # actually preserving order of series list is nice but not strictly required.
            # let's use submit + as_completed to show progress accurately.
            
            future_to_series = {executor.submit(fetch_series_episodes, item, cat_map): item for item in series_list}
            
            for future in concurrent.futures.as_completed(future_to_series):
                count += 1
                if count % 100 == 0:
                    print(f"Processed {count}/{total} series...")
                
                try:
                    result = future.result()
                    if result:
                        f.write(result)
                except Exception as exc:
                    print(f"Generator exception: {exc}")

    print(f"Finished processing {total} series into {filename}")

def fetch_and_save(action, filename, mode, cat_map):
    url = f"{API_URL}?username={USERNAME}&password={PASSWORD}&action={action}"
    print(f"Fetching list {action}...")
    
    try:
        data = fetch_with_retry(url, retries=3, timeout=120)
        
        if not isinstance(data, list):
            print(f"Error: Expected list for {action} but got {type(data)}")
            return

        count = len(data)
        print(f"Fetched {count} items for {filename}.")
        
        if mode == "series":
            # Special concurrent handling for series
            process_series_concurrently(data, cat_map, filename, max_workers=20)
            return

        print(f"Processing {count} items for {filename}...")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(get_m3u_header())
            f.write(f"# Total Items: {count}\n")
            f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')} UTC\n")
            
            for item in data:
                entry = ""
                if mode == "live":
                    entry = format_live_entry(item, cat_map)
                elif mode == "vod":
                    entry = format_vod_entry(item, cat_map)
                
                if entry:
                    f.write(entry)
        
        print(f"Successfully saved {filename} with {count} entries.")

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
    # series_cats = fetch_categories("get_series_categories")
    # fetch_and_save("get_series", "starshare_series.m3u", "series", series_cats)

if __name__ == "__main__":
    main()
