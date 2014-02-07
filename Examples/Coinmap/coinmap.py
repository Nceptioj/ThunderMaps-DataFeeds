#!/usr/bin/env python3
# This could potentially be modified to fetch data from any OpenStreetMap tag.
'''
Created on 21/01/2014
@author: Fraser Thompson
'''
import sys
sys.path.append(r"/usr/local/thundermaps") # /usr/local/thundermaps /home/fraser/Thundermaps/ThunderMaps-DataFeeds
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import logging
import requests
import time, pytz

import Wthundermaps as thundermaps

#LOG_FILENAME = "_errorlog.out"
#logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)

THUNDERMAPS_API_KEY=""
THUNDERMAPS_ACCOUNT_ID="coinmap"

FEED_URL="http://overpass.osm.rambler.ru/cgi/xapi?node[payment:bitcoin=yes][@newer="

SOURCE_ID_FILE=".source_ids_coinmap"

class Feed:
    # Assembles the description to be attached to each report
    def getDescription(self):
        desc_lst = []

        if self.name:
            desc_lst.append("Name: " + self.name)

        if self.city:
            desc_lst.append("City: " + self.city)

        if self.contact_website:
            desc_lst.append("Website: " + "<a href=\"" + self.contact_website + "\">"+self.contact_website+"</a>")

        if self.contact_facebook:
            desc_lst.append("Facebook: " + "<a href=\"" + self.contact_facebook + "\">"+self.contact_facebook+"</a>")

        if self.contact_phone:
            desc_lst.append("Phone: " + self.contact_phone)

        if self.contact_twitter:
            desc_lst.append("Twitter: " + self.contact_twitter)

        if self.opening_hours:
            desc_lst.append("Opening hours: " + self.opening_hours)

        desc_lst.append("</br>" + self.desc)

        desc_str = "</br>".join(desc_lst)
        return desc_str

    def format_feed(self):
        listings = []

        # Work out current time minus a time period
        time = datetime.now() - timedelta(days = 0, hours = 12, minutes = 0, seconds = 0)
        local = pytz.timezone("Pacific/Auckland")
        local_dt = local.localize(time, is_dst = None)
        time_now = local_dt.astimezone(pytz.utc)

        time_str = time_now.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Append the time minus a day to the URL
        url_time = FEED_URL + time_str + "]"

        # Get the things
        print("Getting the feed...")
        r = requests.get(url_time)
        print("Done. Status: " + str(r.status_code))
        root = ET.fromstring(r.content)
        self.num_found = len(root)

        for i in range(2, self.num_found):

            guid = root[i].get('id')
            lat = root[i].get('lat')
            long = root[i].get('lon')

            # Harvesting the attributes
            attr = {}
            for j in range(0, len(root[i])):
                city_dict = dict(root[i][j].attrib)
                attr[city_dict['k']] = city_dict['v']

            self.name = attr.get("name", None)
            self.city = attr.get("addr:city", None)
            self.contact_facebook = attr.get("contact:facebook", None) or attr.get("facebook", None)
            self.contact_website = attr.get("contact:website", None) or attr.get("website", None)
            self.contact_phone = attr.get("contact:phone", None) or attr.get("phone", None)
            self.contact_twitter = attr.get("contact:twitter", None) or attr.get("twitter", None)
            self.opening_hours = attr.get("opening_hours", None)

            self.desc = attr.get("note", "") or attr.get("description", "")

            self.category = attr.get("amenity", None)
            if self.category:
                self.category = self.category.replace("_", " ").capitalize()

            listing = {"occurred_on":time_str,
                       "latitude":lat,
                       "longitude":long,
                       "description": self.getDescription(),
                       "primary_category_name": self.category,
                       "source_id":guid}

            #create a list of dictionaries
            listings.insert(0, listing)
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
#try:
updater.start(6)
#except:
#   logging.exception('Got exception on main handler')
#   raise