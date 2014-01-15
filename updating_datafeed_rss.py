#!/usr/bin/env python

# Scans the RSS feed every half hour and sends events returned by rss.py to Thundermaps.
# Modified from updating_datafeed_caching.py
# Author: Fraser Thompson

import thundermaps
import time
from datetime import datetime
from time import strptime
import rss

THUNDERMAPS_API_KEY = "03a01ba4d1d3c60feec7fe7a4cc832b6"
THUNDERMAPS_ACCOUNT_ID = "gdfgsdfg"
THUNDERMAPS_CATEGORY_ID = {"ISS Sighting": 11870, "CYGNUS Sighting": 11871}

# Try to load the source_ids already posted.
source_ids = []
try:
	source_ids_file = open(".source_ids_sample", "r")
	source_ids = [i.strip() for i in source_ids_file.readlines()]
	source_ids_file.close()
except Exception as e:
	print "! WARNING: No valid cache file was found. This may cause duplicate reports."

# Create an instance of the ThunderMaps class.
tm = thundermaps.ThunderMaps(THUNDERMAPS_API_KEY)

# Lets everyone know what time it is
last_updated = datetime.now()

# Create object for RSS feed
feed_url = 'http://spotthestation.nasa.gov/sightings/xml_files/New_Zealand_None_Wellington.xml' 
feed_obj = rss.Feed(feed_url, last_updated)

# Run until interrupt received.
print "* Updating..."
while True:
	# Load the data which happens since data was last retrieved.
	items = feed_obj.getFeed()

	# Update timestamp of last update.
	last_updated = datetime.now()

	# Create reports for the listings.
	reports = []
	for item in items:
		# Create the report, filling in the fields using fields from the RSS obj
		report = {
			"latitude": -41.2889,
			"longitude": 174.7772,
			"category_id": THUNDERMAPS_CATEGORY_ID[item.getCategory()],
			"occurred_on": item.getDateTime().strftime('%H:%M%p %d/%m/%Y'),
			"description": item.getDescription(),
			}
		# Add the report to the list of reports if it hasn't already been posted.
		if report["occurred_on"] not in source_ids:
			reports.append(report)
		source_ids.append(report["occurred_on"])

	# If there is at least one report, send the reports to Thundermaps.
	if len(reports) > 0:
		print "* Sending", len(reports), "reports to Thundermaps..."
		# Upload 10 at a time.
		for some_reports in [reports[i:i+10] for i in range(0, len(reports), 10)]:
			tm.sendReports(THUNDERMAPS_ACCOUNT_ID, some_reports)
		print "* Done."
				  
	try:
		source_ids_file = open(".source_ids_sample", "w")
		for i in source_ids:
			source_ids_file.write("%s\n" % i)
		source_ids_file.close()
	except Exception as e:
		print "! WARNING: Unable to write cache file."
		print "! If there is an old cache file when this script is next run, it may result in duplicate reports."

	print "* Update completed."

	# Wait half an hour before trying again.
	if reports == []:
		print "* No new entries added."
	time.sleep(30 * 60)
