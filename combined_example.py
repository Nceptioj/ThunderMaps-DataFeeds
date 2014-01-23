#!/usr/bin/env python
'''
Created on 21/01/2014
This is a combined Feed grabber and automatic ThunderMaps updater. It will grab from a feed, generate reports, and post them
to thundermaps at a timed interval. NASA's Spot The Station RSS feed is used as an example. Refer to documentation for more info.
@author: Fraser Thompson
'''

import feedparser
from datetime import datetime
import time
import thundermaps

FEED_URL="http://spotthestation.nasa.gov/sightings/xml_files/New_Zealand_None_Wellington.xml"

THUNDERMAPS_API_KEY=""
THUNDERMAPS_ACCOUNT_ID=""

class Feed:
    def __init__(self, FEED_URL):
        self.feed_url = FEED_URL

    def getFeed(self):
        rss_parsed_top = feedparser.parse(self.feed_url)
        length = len(rss_parsed_top['entries'])
        time_now = datetime.now()
        listings = []

        for i in range(0, length):
            rss_parsed = rss_parsed_top['entries'][i]

            # Extracting fields from the feed data
            title = rss_parsed['title']
            desc = rss_parsed['description']
            guid = rss_parsed['guid']

            # Splitting the description into a dictionary
            desc_dict = self.splitDesc(desc)

            # Extracting fields from description (check field names)
            duration = desc_dict["Duration"]
            category_name = title[11:]
            approach = desc_dict["Approach"]
            departure = desc_dict["Departure"]
            maximum_elevation = int(desc_dict["Maximum Elevation"][:2])
            occured_on = self.makeDateTime(desc_dict)

            # Location data
            latitude = -41.288
            longitude = 174.7772

            # Checks to see if the event happens today and appears over 40 degrees, is visible
            if ((occured_on.day == time_now.day) & (maximum_elevation > 40)):
                listing = {"occurred_on":occured_on.strftime('%d/%m/%Y %I:%M %p'),
                    "latitude": latitude,
                    "longitude": longitude,
                    "description": self.getDescription(approach, departure, duration),
                    "category_name":category_name + " - NASA Alert",
                    "source_id": guid}
                # Adds the report to the list of valid entries
                listings.insert(0, listing)

        return listings

    @staticmethod
    def getDescription(approach, departure, duration):
        description_str = "Travelling from " + approach + " to " + departure + " for " + duration + "."
        return description_str

    @staticmethod
    def makeDateTime(string):
        updated_str = string['Date'] + " " + string['Time']

        # Because NASA formats their times inconsistently...
        format_12 = '%A %b %d, %Y %I:%M %p'
        format_24 = '%A %b %d, %Y %H:%M %p'
        try:
            updated_obj = datetime.strptime(updated_str, format_12)
        except ValueError:
            updated_obj = datetime.strptime(updated_str, format_24)

        return updated_obj

    @staticmethod
    def splitDesc(desc):
        desc = " ".join(desc.split())
        desc_dict = dict(item.split(': ') for item in desc.split(' <br/> '))
        desc_dict["Departure"] = desc_dict["Departure"][:-6] #because of a pesky regex thing, not usually necessary
        return desc_dict

class Updater:
    def __init__(self, key, account_id):
        self.tm_obj = thundermaps.ThunderMaps(key)
        self.feed_obj = Feed(FEED_URL)
        self.account_id = account_id

    def start(self, update_interval=-1):
        # Try to load the source_ids already posted.
        source_ids = []
        try:
            source_ids_file = open(".source_ids_sample", "r")
            source_ids = [i.strip() for i in source_ids_file.readlines()]
            source_ids_file.close()
        except Exception as e:
            print("! WARNING: No valid cache file was found. This may cause duplicate reports.")

        # Run until interrupt received.
        while True:
            # Load the data from the data feed.
            # This method should return a list of dicts.
            items = self.feed_obj.getFeed()

            # Create reports for the listings.
            reports = []
            for report in items:
                # Add the report to the list of reports if it hasn't already been posted.
                if report["source_id"] not in source_ids:
                    reports.append(report)
                    print("Adding %s" % report["description"])
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
                source_ids_file = open(".source_ids_store", "w")
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
updater.start()
