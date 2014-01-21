#!/usr/bin/env python
'''
Created on 21/01/2014
This is a combined Feed grabber and automatic ThunderMaps updater. It will grab from a feed, generate reports, and post them
to thundermaps at a timed interval. Refer to documentation for more info.
@author: Fraser Thompson
'''

import feedparser
from datetime import datetime
import time, pytz
import re
import thundermaps

FEED_URL="http://feeds.feedburner.com/malaysiacrime/latest.xml"

THUNDERMAPS_API_KEY=""
THUNDERMAPS_ACCOUNT_ID="malaysia-crime-reports"

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

            #for thing in rss_parsed:
             #       print(thing)

            # Extracting fields from the feed data
            title = rss_parsed['title']
            desc = rss_parsed['description']
            guid = rss_parsed['guid']
            georss = rss_parsed['georss_point']
            occured_on = self.makeDateTime(rss_parsed['published'])

            # Formatting description
            desc = re.sub('<[^>]*>', '', desc)
            desc = desc[:300].strip() + "..." + " Read more: " + guid
            # Location data
            latitude = float(georss.split()[0])
            longitude = float(georss.split()[1])

            # Checks to see if the event happens today and appears over 40 degrees, is visible
            if occured_on.day == time_now.day:
                listing = {"occurred_on":occured_on.strftime('%d/%m/%Y %I:%M %p'),
                    "latitude": latitude,
                    "longitude": longitude,
                    "description": desc,
                    "category_name": "Malaysia Crime Reports",
                    "source_id": guid}
                # Adds the report to the list of valid entries
                listings.append(listing)

        return listings

    @staticmethod
    def makeDateTime(string):
        format_12 = '%a, %d %b %Y %H:%M:%S +0800'
        naive = datetime.strptime(string, format_12)

        local = pytz.timezone("Asia/Kuala_Lumpur")
        local_dt = local.localize(naive, is_dst = None)
        utc_dt = local_dt.astimezone(pytz.utc)
        return utc_dt

    @staticmethod
    def splitDesc(desc):
        desc = " ".join(desc.split())
        desc_dict = dict(item.split(': ') for item in desc.split(' <br/> '))
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
                source_ids_file = open(".source_ids_sample", "w")
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
                update_interval = (t + 24*3600 - time.time())
                print("* Will check again tomorrow.")
            else:
                # Convert hours into seconds
                update_interval = update_interval*60*60
                print("* Will check again in", update_interval, "hour(s).")

            time.sleep(update_interval)

updater = Updater(THUNDERMAPS_API_KEY, THUNDERMAPS_ACCOUNT_ID)
updater.start()