#!/usr/bin/env python
# Used to update Thundermaps with ISS sightings from NASA's spot the station.

import updater

# Key, account, categories...
THUNDERMAPS_API_KEY = ""
THUNDERMAPS_ACCOUNT_ID = ""
RSS_FEED_URL = 'http://spotthestation.nasa.gov/sightings/xml_files/New_Zealand_None_Wellington.xml'

# Create updater
rss_updater = updater.Updater(THUNDERMAPS_API_KEY, THUNDERMAPS_ACCOUNT_ID, RSS_FEED_URL)

# Start updating
rss_updater.start()
