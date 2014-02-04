#!/usr/bin/env python3
'''
Created on 21/01/2014
@author: Fraser Thompson
'''
import sys
sys.path.append(r"/home/fraser/Thundermaps/ThunderMaps-DataFeeds")
import time
from datetime import datetime
import Pthundermaps as thundermaps
import requests

INSTAGRAM_ID=""
INSTAGRAM_SECRET=""

THUNDERMAPS_API_KEY=""
THUNDERMAPS_ACCOUNT_ID="instagram"

SOURCE_ID_FILE = ".source_ids_instagram"

class Feed:
    def __init__(self, INSTAGRAM_ID, INSTAGRAM_SECRET):
        self.instagram_id = INSTAGRAM_ID
        self.instagram_secret = INSTAGRAM_SECRET

    # Assembles the description to be attached to each report
    def getDescription(self):
        desc_lst = []
        #Description
        desc_lst.append("'" + self.title + "'" + " by " + self.username + (( " at " + self.loc_name + ".") if self.loc_name != None else "."))
        desc_lst.append("</br>" + self.likes + " likes")
        #Image
        desc_lst.append("</br><a href=\"" + self.url + "\">"+"See image on Instagram"+"</a>")
        desc_str = "</br>".join(desc_lst)
        return desc_str

    def format_feed(self):
        listings = []
        c_time = str(time.time()-3600)

        # Number of pages to go through before stopping. Going further will obvs produce more reports.
        max_pages = 2

        # Tag we're looking for
        tag = "nature"

        # Starting URL sorted by most recent tagged
        r_url = "https://api.instagram.com/v1/tags/"+tag+"/media/recent?&count=64&min_timestamp="+c_time+"&client_id="+self.instagram_id

        while max_pages > 0:
            print("Pages left:", max_pages)
            r = requests.get(r_url)
            print("Status:", r.status_code)

            data = r.json()
            entries = data['data']
            num_found = len(entries)

            for i in range(0, num_found):
                caption = entries[i].get('caption', None)
                location = entries[i].get('location', None)
                media_type = entries[i]['type']

                # Skip if there's no caption data
                if caption is None:
                    continue

                # Skip if it's a video
                if media_type is "video":
                    continue

                # Skip if there's no geodata
                if location is None:
                    print("no location data")
                    continue
                else:
                    lat = location.get('latitude', None)
                    long = location.get('longitude', None)
                    if lat is None:
                        continue

                date = datetime.fromtimestamp(int(entries[i]['caption']['created_time'])).strftime('%Y-%m-%d %H:%M:%S')
                guid = caption['id']

                self.title = caption['text']
                self.username = caption['from']['username']

                self.likes = str(entries[i]['likes']['count'])
                self.url = entries[i]['link']
                self.image = entries[i]['images']['standard_resolution']['url']

                self.loc_name = location.get('name', None)

                listing = {"occurred_on":date,
                           "latitude":lat,
                           "longitude":long,
                           "description": self.getDescription(),
                           "source_id":guid,
                           "attachment_url":self.image}

                #create a list of dictionaries
                listings.insert(0, listing)

            #paginate
            r_url = data['pagination']['next_url']
            max_pages = max_pages -1

        print("Sending:", len(listings), "reports to ThunderMaps.")
        return listings

class Updater:
    def __init__(self, key, account_id):
        self.tm_obj = thundermaps.ThunderMaps(key)
        self.feed_obj = Feed(INSTAGRAM_ID, INSTAGRAM_SECRET)
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
updater.start(1)