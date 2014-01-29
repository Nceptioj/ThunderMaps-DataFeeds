#!/usr/bin/env python3
'''
Created on 21/01/2014
This is a combined Feed grabber and automatic ThunderMaps updater. It will grab from a feed, generate reports, and post them
to thundermaps at a timed interval. Refer to documentation for more info.
@author: Fraser Thompson
'''
import logging
from datetime import datetime, timedelta
import sys
sys.path.append(r"/home/fraser/Thundermaps/ThunderMaps-DataFeeds")
import time, pytz
import requests
import thundermaps

LOG_FILENAME = "_errorlog.out"
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)


THUNDERMAPS_API_KEY=""
THUNDERMAPS_ACCOUNT_ID="zoopla-property-alerts"
AREA="Oxford"

class Feed:

    def getFeed(self):
        listings = []

        # Max pages to check (100 listings per page)
        max_pages = 5
        escape = False

        # Iterate pages
        for i in range (1, max_pages):
            print("checking page " + str(i))
            remotedata = requests.get("http://api.zoopla.co.uk/api/v1/property_listings.js?area="+AREA+"&api_key=4hgz7nf49nd2fkw9av63rpnm&page_size=100&order_by=age&summarised=true&page_number=" + str(i))
            rt_tree = remotedata.json()

            # Finding current time and making it timezone aware
            time_naive = datetime.now()
            local = pytz.timezone("Pacific/Auckland")
            local_dt = local.localize(time_naive, is_dst = None)
            time_now = local_dt.astimezone(pytz.utc)

            length = len(rt_tree["listing"])

            # Iterate listings
            for j in range(0, length):
                thing = rt_tree["listing"][j]

                # Checks only events from the past time interval
                # This is the interval to check backwards into
                margin = timedelta(minutes = 0, hours = 12, days = 0, seconds = 0)
                occured_on = self.makeDateTime(thing["last_published_date"])

                # Skip it if it's too old, stop checking on next page
                if ((time_now - margin) > occured_on):
                    escape = True
                    continue

                self.url = thing["image_url"]
                self.thumb_url = thing["thumbnail_url"]
                self.caption = thing["image_caption"]
                self.guid = thing["details_url"]

                self.address = thing["displayable_address"]
                self.description = thing["description"]
                self.price = int(thing["price"])
                self.num_bedrooms = thing["num_bedrooms"]
                self.num_bathrooms = thing["num_bathrooms"]
                self.first_listed = thing["first_published_date"]
                self.status = thing["listing_status"]

                latitude = thing["latitude"]
                longitude = thing["longitude"]
                category_name = thing["property_type"]

                listing = {"occurred_on":occured_on.strftime('%d/%m/%Y %I:%M %p'),
                    "latitude": latitude,
                    "longitude": longitude,
                    "description": self.getDescription(),
                    "category_name":(category_name if category_name != "" else self.num_bedrooms + " bedrooms") + " for "+ self.status + " - Zoopla Property Alert",
                    "attachment_url": self.url,
                    "source_id": self.guid}

                # Adds the report to the list of valid entries
                listings.insert(0, listing)

            # Stop checking pages
            if escape == True:
                break

        print(len(listings))
        return listings

    # Assembles the description to be attached to each report
    def getDescription(self):
        desc_lst = []
        # Description
        desc_lst.append("<strong>First listed: £" + "{0:,}".format(self.price) + " on " + self.first_listed + "</strong>")
        desc_lst.append("<strong>Num Bedrooms: " + self.num_bedrooms + "</strong>")
        desc_lst.append("<strong>Num Bathrooms: " + self.num_bathrooms + "</strong></br>")
        desc_lst.append(self.description + "<a href=\"" + self.guid + "\">" + " read more</a>")
        # Image
        desc_lst.append("<a href=\"" + self.guid + "\"><br><img title=\"Click for larger view\" src=\"" + self.url + "\" alt=\"Click for larger view\"></a></br>")
        # Add caption to image if there is one
        if self.caption != "":
            desc_lst.append("'" + self.caption + "'<br>")
        # Add Zoopla logo
        desc_lst.append('<a href="http://www.zoopla.co.uk/"><img src="http://www.zoopla.co.uk/static/images/mashery/powered-by-zoopla.png" width="111" height="54" title="Property information powered by Zoopla" alt="Property information powered by Zoopla" border="0"&gt;</a>')
        return "</br>".join(desc_lst)

    def makeDateTime(self, string):
        format_12 = '%Y-%m-%d %H:%M:%S'
        updated_obj = datetime.strptime(string, format_12)

        # Make it timezone aware
        local = pytz.timezone("Europe/London")
        local_dt = local.localize(updated_obj, is_dst = None)
        utc_dt = local_dt.astimezone(pytz.utc)
        return utc_dt

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
                    for report in some_reports:
                        # Add image
                        image_id = self.tm_obj.uploadImage(report["attachment_url"])
                        if image_id != None:
                            print("[%s] Uploaded image for listing %s..." % (time.strftime("%c"), report["source_id"]))
                            report["attachment_ids"] = [image_id]
                        del report["attachment_url"]
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
try:
    updater.start(1)
except:
    logging.exception('Got exception on main handler')
    raise