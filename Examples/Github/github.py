#!/usr/bin/env python
'''
Created on 21/01/2014
@author: Fraser Thompson
'''

import feedparser
import requests, json
import time, pytz
from datetime import timedelta
from datetime import datetime
import sys
sys.path.append(r"/home/fraser/Thundermaps/ThunderMaps-DataFeeds")
import thundermaps
from geopy import geocoders

THUNDERMAPS_API_KEY=""
THUNDERMAPS_ACCOUNT_ID="github-public-feed"

class Feed:

    # Used internally to print all fields per entry in a new feed so you know what is contained in the data
    def printFields(self):
        for i in range(0, len(self.entries)):
            for thing in self.entries[i]:
                print(thing)
                print("\t", self.entries[i][thing])

    # Assembles the description to be attached to each report
    def getDescription(self):
        desc_lst = []
        desc_lst.append(self.desc)
        desc_lst.append("Occurred on: " + self.date)
        desc_str = "</br>".join(desc_lst)
        return desc_str

    def format_feed(self):
        #self.printFields()
        time_now = datetime.now()
        local = pytz.timezone("Pacific/Auckland")
        local_dt = local.localize(time_now, is_dst = None)
        time_now = local_dt.astimezone(pytz.utc)
        token = "70ed49afaec90db1380a45e379b7185ff29d8e60"

        listings = []
        more = True

        while more:
            # iterate pages up to page five
            for j in range(0, 5):
                self.r = feedparser.parse("https://github.com/timeline?page="+str(j))
                self.entries = self.r['entries']
                self.num_found = len('entries')

                # iterate entries
                for i in range(0, self.num_found):
                    entry = self.entries[i]
                    author = entry['authors'][0]['name']
                    user = requests.get('https://api.github.com/users/' + author, auth=('Nceptioj', token))
                    user_text = json.loads(user.text or user.content)

                    self.date = entry['updated']
                    self.date_obj = self.makeDateTime()

                    # If it's too old skip it
                    margin = timedelta(days = 0, hours = 0, minutes = 0, seconds = 2)
                    if self.date_obj < time_now - margin:
                        print("Old. Skipping")
                        more = False
                        continue

                    # If something is wrong with that one, skip it
                    if(user.ok != True):
                        print("Malformed user: " + str(user.status_code) + " error.")
                        print(user_text)
                        continue

                    # Get the location from user
                    print("Fetching user data")
                    lat = None
                    long = None
                    try:
                        location = user_text['location']
                        lat = self.geocoder(location)[1][0]
                        long = self.geocoder(location)[1][1]
                    except KeyError:
                        print("No location data for user")
                    except TypeError:
                        print("Something broken")

                    # If there's no location data skip it
                    if lat == None or long == None:
                        print("Could not geocode location, skipping")
                        continue

                    self.url = entry['link']
                    self.title = entry['title']
                    self.guid = entry['id']
                    desc_raw = entry['content'][0]['value']
                    desc = desc_raw.split("<div class=\"title\">\n  ")[1]
                    self.desc = desc.split("</div>")[0].strip()

                    listing = {"occurred_on":self.date,
                               "latitude":lat,
                               "longitude":long,
                               "description": self.getDescription(),
                               "category_name":" Github Public Feed",
                               "source_id":self.guid,}

                    #create a list of dictionaries
                    listings.insert(0, listing)
                    print(listing)
        print(len(listings))
        #return listings

    def makeDateTime(self):
        format_12 = '%Y-%m-%dT%H:%M:%SZ'
        naive = datetime.strptime(self.date, format_12)
        local = pytz.timezone("UTC")
        local_dt = local.localize(naive, is_dst = None)
        utc_dt = local_dt.astimezone(pytz.utc)
        return utc_dt

    def geocoder(self, address):
        #Geocodes addresses using the GoogleV3 package. This converts addresses to lat/long pair
        try:
            # Trying to avoid being locked out
            #time.sleep(1)
            g = geocoders.GoogleV3()
            (lat, long) = g.geocode(address)
            if (lat, long) == 'None':
                pass
            else:
                return (lat, long)
        except TypeError:
            pass
        except geocoders:
            print("Quota for geocoder API key exceeded!")
            time.sleep(3)
            pass

class Updater:
    def __init__(self, key, account_id):
        self.tm_obj = thundermaps.ThunderMaps(key)
        self.feed_obj = Feed()
        self.account_id = account_id

    def start(self, update_interval=-1):
        # Try to load the source_ids already posted.
        source_ids = []
        try:
            source_ids_file = open(".source_ids_flickrnz", "r")
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
                source_ids_file = open(".source_ids_flickrnz", "w")
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