#!/usr/bin/env python3
'''
Created on 21/01/2014
@author: Fraser Thompson
'''
import sys
sys.path.append(r"/usr/local/thundermaps") #/home/fraser/Thundermaps/ThunderMaps-DataFeeds
import time, pytz
from datetime import datetime, timedelta
import Pthundermaps_staging as thundermaps
import requests

COUPONS_KEY=""
THUNDERMAPS_API_KEY=""
THUNDERMAPS_ACCOUNT_ID="8coupons-testing"

SOURCE_ID_FILE = ".source_ids_8coupons"

class Feed:

    # Assembles the description to be attached to each report
    def getDescription(self):
        desc_lst = []
        #Description
        desc_lst.append('<strong>' + self.title + ' at ' + self.name + '</strong>')
        #link
        desc_lst.append("</br><a href=\"" + self.url + "\">"+"Get this deal!"+"</a>")
        #Expiry
        desc_lst.append('</br>Expires: ' + self.expires)
        #logo
        desc_lst.append("</br><a href=\"http://www.8coupons.com\"><br><img title=\"Powered by 8 Coupons\"src=\"http://8coupons.com/static_new/images/graphics/8coupons-med.png\"alt=\"Powered by 8Coupons\"></a></br>")
        desc_str = "</br>".join(desc_lst)
        return desc_str

    def format_feed(self):
        listings = []

        # Getting current date/time and converting into timezone aware object
        now_naive = datetime.now()
        local = pytz.timezone("Pacific/Auckland")
        local_dt = local.localize(now_naive, is_dst = None)
        now = local_dt.astimezone(pytz.utc)

        margin = timedelta(hours = 12, days = 0, minutes = 0, seconds = 0)

        r_url = "http://api.8coupons.com/v1/getrealtimelocaldeals?key="+COUPONS_KEY+"&categoryid=2,6"
        r = requests.get(r_url)
        print("Status:", r.status_code)

        entries = r.json()

        for i in range(0, 500):
            lat = entries[i]['lat']
            long = entries[i]['lon']

            # Getting the date/time and turning into a timezone aware object
            date = entries[i]['postDate']
            date_naive = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            local = pytz.timezone("US/Eastern")
            local_dt = local.localize(date_naive, is_dst = None)
            date_obj = local_dt.astimezone(pytz.utc)

            # Get out if it starts getting too old
            if date_obj < (now - margin):
                break

            guid = entries[i]['ID']
            category = entries[i]['categoryID']

            if category == '2':
                category_name = 'Entertainment'
            elif category == '6':
                category_name = 'Shopping'

            self.name = entries[i]['name']
            self.city = entries[i]['city']
            self.title = entries[i]['dealTitle']
            self.url = entries[i]['URL']
            self.image = entries[i]['showImage']
            self.expires = entries[i]['expirationDate']


            listing = {"occurred_on":date,
                       "latitude":lat,
                       "longitude":long,
                       "description": self.getDescription(),
                       "source_id":guid,
                       "primary_category_name": "8Coupons Testing",
                       "secondary_category_name": category_name,
                       "attachment_url":self.image}

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
updater.start(6)