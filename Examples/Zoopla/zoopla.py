#!/usr/bin/env python
'''
Created on 21/01/2014
This is a combined Feed grabber and automatic ThunderMaps updater. It will grab from a feed, generate reports, and post them
to thundermaps at a timed interval. Refer to documentation for more info.
@author: Fraser Thompson
'''

from datetime import datetime, timedelta
import time
import requests
import thundermaps

THUNDERMAPS_API_KEY=""
THUNDERMAPS_ACCOUNT_ID="zoopla-property-alerts"

class Feed:

    def getFeed(self):
        remotedata = requests.get("http://api.zoopla.co.uk/api/v1/property_listings.js?area=Oxford&api_key=4hgz7nf49nd2fkw9av63rpnm&page_size=100&order_by=age")
        rt_tree = remotedata.json()

        time_now = datetime.now()
        length = len(rt_tree["listing"])
        print(rt_tree["result_count"])
        listings = []

        for i in range(0, length):
            thing = rt_tree["listing"][i]

            self.address = thing["displayable_address"]
            self.description = thing["short_description"]
            self.url = thing["image_url"]
            self.thumb_url = thing["thumbnail_url"]
            self.bedrooms = thing["num_bedrooms"]
            self.price = int(thing["price"])
            self.num_bedrooms = thing["num_bedrooms"]
            self.guid = thing["details_url"]
            self.first_listed = thing["first_published_date"]
            self.status = thing["listing_status"]

            latitude = thing["latitude"]
            longitude = thing["longitude"]
            category_name = thing["property_type"]
            occured_on = self.makeDateTime(thing["last_published_date"])

            # Checks only events from the past day
            margin = timedelta(days = 1)
            if (time_now - margin < occured_on):
                listing = {"occurred_on":occured_on.strftime('%d/%m/%Y %I:%M %p'),
                    "latitude": latitude,
                    "longitude": longitude,
                    "description": self.getDescription(),
                    "category_name":(category_name if category_name != "" else self.num_bedrooms + " bedrooms") + " for "+ self.status + " - Zoopla Property Alert",
                    "source_id": self.guid}
                # Adds the report to the list of valid entries
                listings.insert(0, listing)
        print(len(listings))
        return listings

    def getDescription(self):
        desc_lst = []
        desc_lst.append("<a href=\"" + self.guid + "\"><br><img title=\"Click for larger view\" src=\"" + self.url + "\" alt=\"Click for larger view\"></a></br>")
        desc_lst.append("<strong>First listed: £" + "{0:,}".format(self.price) + " on " + self.first_listed + "</strong>")
        desc_lst.append(self.description + "<a href=\"" + self.guid + "\">" + " read more</a>")
        return "</br>".join(desc_lst)

    def makeDateTime(self, string):
        format_12 = '%Y-%m-%d %H:%M:%S'
        updated_obj = datetime.strptime(string, format_12)
        return updated_obj

class Updater:
    def __init__(self, key, account_id):
        self.tm_obj = thundermaps.ThunderMaps(key)
        self.feed_obj = Feed()
        self.account_id = account_id

    def start(self, update_interval=-1):
        # Try to load the source_ids already posted.
        source_ids = []
        try:
            source_ids_file = open(".source_ids_zoopla", "r")
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
                source_ids_file = open(".source_ids_zoopla", "w")
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