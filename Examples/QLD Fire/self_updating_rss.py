#!/usr/bin/env python
# Used to update Thundermaps with events from QLD Fire.

import updater

# Key, account, categories...
THUNDERMAPS_API_KEY = ""
THUNDERMAPS_ACCOUNT_ID = ""
RSS_FEED_URL = 'http://www.rfs.nsw.gov.au/feeds/majorIncidents.xml'

# Create updater
fire_updater = updater.Updater(THUNDERMAPS_API_KEY, THUNDERMAPS_ACCOUNT_ID, RSS_FEED_URL)

# Start updating
fire_updater.start()
