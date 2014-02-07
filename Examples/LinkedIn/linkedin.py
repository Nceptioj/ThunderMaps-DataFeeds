#!/usr/bin/env python
'''
Created on 22/01/2014
This is a combined Feed grabber and automatic ThunderMaps updater. It will grab from a feed, generate reports, and post them
to thundermaps at a timed interval. Refer to documentation for more info.
@author: Fraser Thompson
'''
from datetime import datetime
import sys
sys.path.append(r"/home/fraser/Thundermaps/ThunderMaps-DataFeeds") #/home/fraser/Thundermaps/ThunderMaps-DataFeeds /usr/local/thundermaps
import time, pytz
import requests
import thundermaps

LINKEDIN_KEY = ""
LINKEDIN_SECRET = ""

THUNDERMAPS_API_KEY=""
THUNDERMAPS_ACCOUNT_ID=""

SOURCE_ID_FILE = ".source_ids_linkedin"

class Feed:

    def format_feed(self):
        listings = []

        r_url = "https://www.eventbrite.com/json/event_search?category=music%2C%20entertainment%2C%20performances&date=Future&date_created=Yesterday&max=100&page="+str(i)+"&app_key=" + FEED_KEY
        r = requests.get(r_url)
        print("Status:", r.status_code)

        data = r.json()
        entries = data['events']

        for i in range(1, len(entries)):
            try:
                lat = entries[i]['event']['venue']['latitude']
                long = entries[i]['event']['venue']['longitude']
                venue_name = entries[i]['event']['venue']['name']
            except KeyError:
                continue

            date = entries[i]['event']['created']
            guid = entries[i]['event']['id']

            self.category_name = entries[i]['event']['category']
            self.formatCategory()
            self.desc = entries[i]['event']['description']
            self.title = entries[i]['event']['title']
            self.startdate = entries[i]['event']['start_date']
            self.enddate = entries[i]['event']['end_date']
            self.url = entries[i]['event']['url']

            listing = {"occurred_on":date,
                       "latitude":lat,
                       "longitude":long,
                       "description": self.getDescription(),
                       "source_id":guid,
                       "primary_category_name": self.primary_category,
                       "secondary_category_name": self.secondary_category,}

            #create a list of dictionaries
            listings.insert(0, listing)

        print("Sending:", len(listings), "reports to ThunderMaps.")
        return listings

class Updater:
    def __init__(self, key, account_id):
        self.tm_obj = thundermaps.ThunderMaps(key)
        self.feed_obj = Feed()
        self.account_id = account_id

    def start(self, update_interval=-1):
        # Try to load the source_ids already posted.
        source_ids = []
        try:
            source_ids_file = open(SOURCE_ID_FILE, "r")
            source_ids = [i.strip() for i in source_ids_file.readlines()]
            source_ids_file.close()
        except Exception as e:
            print("! WARNING: No valid cache file was found. This may cause duplicate reports.")

        # Run until interrupt received.
        while True:
            # Load the data from the data feed.
            # This method should return a list of dicts.
            items = self.feed_obj.format_feed()

            # Create reports for the listings.
            reports = []
            for report in items:

                # Add the report to the list of reports if it hasn't already been posted.
                if report["source_id"] not in source_ids:
                    reports.append(report)
                    print("Adding %s" % report["source_id"])

                    # Add the source id to the list.
                    source_ids.append(report["source_id"])

            # If there is at least one report, send the reports to Thundermaps.
            if len(reports) > 0:
                # Upload 10 at a time.
                for some_reports in [reports[i:i+10] for i in range(0, len(reports), 10)]:
                    print("Sending %d reports..." % len(some_reports))
                    self.tm_obj.sendReports(self.account_id, some_reports)
                    time.sleep(3)

            # Save the posted source_ids.
            try:
                source_ids_file = open(SOURCE_ID_FILE, "w")
                for i in source_ids:
                    source_ids_file.write("%s\n" % i)
                source_ids_file.close()
            except Exception as e:
                print("! WARNING: Unable to write cache file.")
                print("! If there is an old cache file when this script is next run, it may result in duplicate reports.")

            # Waiting the update interval
            # If updating daily
            if update_interval < 0:
                t = time.localtime()
                t = time.mktime(t[:3] + (0, 0, 0) + t[6:])
                update_interval_s = (t + 24*3600 - time.time())
                print("* Will check again tomorrow.")
            else:
                # Convert hours into seconds
                update_interval_s = update_interval*60*60

                if update_interval < 1:
                    print("* Will check again in", update_interval_s, "seconds.")
                else:
                    print("* Will check again in", update_interval, "hours.")

            time.sleep(update_interval_s)

updater = Updater(THUNDERMAPS_API_KEY, THUNDERMAPS_ACCOUNT_ID)
updater.start(24)