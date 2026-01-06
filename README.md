# IPTV M3U Auto-Generator

This repository contains a setup to automatically fetch IPTV channels and movies from your server and generate `starsharetv.m3u` and `starsharemovie.m3u` every 12 hours.

## Setup

1.  **Usage**:
    The GitHub Actions workflow is scheduled to run automatically every 12 hours.
    It will:
    -   Fetch the latest Live and VOD streams from the API.
    -   Generate `starsharetv.m3u` (Live Channels).
    -   Generate `starsharemovie.m3u` (Movies).
    -   Commit the updated files back to this repository.

2.  **Manual Update**:
    You can manually trigger the update by going to the "Actions" tab in your GitHub repository, selecting "Update IPTV Playlists", and clicking "Run workflow".

3.  **Files**:
    -   `generate_m3u.py`: The Python script that does the work.
    -   `.github/workflows/update_m3u.yml`: The automation schedule.
    -   `requirements.txt`: Dependencies.

## Credentials

Currently, the credentials are included in the script as configured. If you wish to change them, edit `generate_m3u.py` or switch to using GitHub Secrets for better security.

## Output

After the action runs, you will see two files in your repository:
-   `starsharetv.m3u`
-   `starsharemovie.m3u`

You can use the "Raw" link of these files in your IPTV player.
