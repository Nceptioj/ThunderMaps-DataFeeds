#!/usr/bin/env python
'''
Created on 21/01/2014
This is a combined Feed grabber and automatic ThunderMaps updater. It will grab from a feed, generate reports, and post them
to thundermaps at a timed interval. NASA's Spot The Station RSS feed is used as an example. Refer to documentation for more info.
@author: Fraser Thompson
'''

import feedparser, requests
from datetime import datetime, timedelta
import time, pytz
import re
import thundermaps
import os
from geopy import geocoders

FEED_URL="http://www.trumba.com/calendars/seattlegov-city-wide.rss"

THUNDERMAPS_API_KEY=""
THUNDERMAPS_ACCOUNT_ID=""

class Feed:
    def __init__(self, FEED_URL):
        self.feed_url = FEED_URL

    def getFeed(self):

        # Storing a local copy because there's like 500 elements
        if not os.path.exists('local_copy.xml'):
            print("Opening HTTP request...")
            r = requests.get(FEED_URL, stream=True)
            print("Request opened.")

            try:
                    with open('local_copy.xml', 'wb') as f:
                        print("Writing file...")
                        for chunk in r.iter_content(chunk_size=1024):
                            if chunk:
                                f.write(chunk)
                                f.flush()
            except IOError:
                print("IOError")

        rss_parsed_top = feedparser.parse(r'local_copy.xml')

        #length = len(rss_parsed_top['entries'])
        count = 0

        time_nows = datetime.now()
        local = pytz.timezone("Pacific/Auckland")
        local_dt = local.localize(time_nows, is_dst = None)
        time_now = local_dt.astimezone(pytz.utc)

        listings = []

        for i in range(0, 20):
            rss_parsed = rss_parsed_top['entries'][i]

            # Extracting fields from the feed data
            title = rss_parsed['title']
            desc = rss_parsed['description']
            guid = rss_parsed['guid']

            # Splitting the description into a dictionary
            desc_dict = self.splitDesc(desc)

            # Extracting fields from description only if they exist
            category_name = "Event"
            if "Event Types" in desc_dict:
                category_name = desc_dict["Event Types"]

            occured_on = self.makeDateTime(desc_dict["Date"])

            description_in = None
            if "Description" in desc_dict:
                description_in = desc_dict["Description"]

            neighborhoods = None
            if "Neighborhoods" in desc_dict:
                neighborhoods = desc_dict["Neighborhoods"]

            contact = None
            if "Contact" in desc_dict:
                contact = desc_dict["Contact"]

            phone = None
            if "Contact Phone" in desc_dict:
                phone = desc_dict["Contact Phone"]

            email = None
            if "Contact Email" in desc_dict:
                email = desc_dict["Contact Email"]

            audience = None
            if "Audience" in desc_dict:
                audience = desc_dict["Audience"]

            pre = None
            if "Pre-Register" in desc_dict:
                pre = desc_dict["Pre-Register"]

            cost = None
            if "Cost" in desc_dict:
                cost = desc_dict["Cost"]

            description = self.getDescription(description_in, neighborhoods, contact, phone, email, audience, pre, cost)

            # Location data
            latitude = None
            if desc_dict["Latitude"] != None:
                latitude = desc_dict["Latitude"]

            longitude = None
            if desc_dict["Longitude"] != None:
                longitude = desc_dict["Longitude"]

            # Checks to see if the event happens in the next 3 days an has geo data
            margin = timedelta(days = 3)
            if ((time_now < occured_on < time_now + margin) & (latitude != None)):
                listing = {"occurred_on":occured_on.strftime('%d/%m/%Y %I:%M %p'),
                    "latitude": latitude,
                    "longitude": longitude,
                    "description": description,
                    "category_name":category_name + " - Seattle Events",
                    "source_id": guid}
                # Adds the report to the list of valid entries
                count = count + 1
                print(listing)
                listings.append(listing)

        print("Found", count, "events.")
        return listings

    def getDescription(self, description, neighborhoods, contact, phone, email, audience, pre, cost):
        description_lst = []

        part_1 = None
        if description != None:
            part_1 = "Description: " + description + "<br/>"
            description_lst.append(part_1)

        part_2 = None
        if neighborhoods != None:
            part_2 = "Neighborhoods: " + neighborhoods + "<br/>"
            description_lst.append(part_2)

        part_3 = None
        if contact != None:
            part_3 = "Contact: " + contact + "<br/>"
            description_lst.append(part_3)

        part_4 = None
        if phone != None:
            part_4 = "Phone: " + phone + "<br/>"
            description_lst.append(part_4)
        part_5 = None
        if email != None:
            part_5 = "Email: " + email + "<br/>"
            description_lst.append(part_5)

        part_6 = None
        if audience != None:
            part_6 = "Audience: " + audience + "<br/>"
            description_lst.append(part_6)

        part_7 = None
        if pre != None:
            part_7 = "Pre-Entry: " + pre + "<br/>"
            description_lst.append(part_7)

        part_8 = None
        if cost != None:
            part_8 = "Cost: " + cost + "<br/>"
            description_lst.append(part_8)

        description_str = " ".join(description_lst)
        return description_str

    def makeDateTime(self, string):
        # Because their formatting is completely inconsistent...
        format_time = '%A, %B %d, %Y %I:%M%p'
        format_time2 = '%A, %B %d, %Y, %I%p'
        format_time3 = '%A, %B %d, %Y, %I:%M'
        format_time4 = '%A, %B %d, %Y, %I'
        format_time5 = '%A, %B %d, %Y, %I:%M%p'
        format_time6 = '%A, %B %d, %I%p'
        format_time7 = '%A, %B %d'
        format_no = '%A, %B %d, %Y'
        updated_obj = None

        # This probably isn't good practice
        try:
            updated_obj = datetime.strptime(string, format_time)
        except ValueError:
            try:
                updated_obj = datetime.strptime(string, format_time2)
            except ValueError:
                try:
                    updated_obj = datetime.strptime(string, format_no)
                except ValueError:
                    try:
                        updated_obj = datetime.strptime(string, format_time3)
                    except ValueError:
                        try:
                            updated_obj = datetime.strptime(string, format_time4)
                        except ValueError:
                            try:
                                updated_obj = datetime.strptime(string, format_time5)
                            except ValueError:
                                try:
                                    updated_obj = datetime.strptime(string, format_time6)
                                except ValueError:
                                    try:
                                        updated_obj = datetime.strptime(string, format_time7)
                                    except ValueError:
                                        print("Oh no!")

        local = pytz.timezone("US/Pacific")
        local_dt = local.localize(updated_obj, is_dst = None)
        utc_dt = local_dt.astimezone(pytz.utc)

        return utc_dt

    def geocoder(self, address):
        #Geocodes addresses using the GoogleV3 package. This converts addresses to lat/long pairs
        try:
            g = geocoders.GoogleV3()
            (lat, long) = g.geocode(address)
            if (lat, long) == 'None':
                pass
            else:
                return (lat, long)
        except TypeError:
            pass

    # Figuring out the extremely annoyingly formatted description.
    def splitDesc(self, desc):
        desc = " ".join(desc.split())

        # Seperate address/date from rest
        working_desc = re.split('<br/><br/>', desc)
        firstpart = re.split('<br/>|<br />', working_desc.pop(0))

        # Split date and time away from address
        date = firstpart.pop(-1)
        date_front = date.split("&")
        date = date_front[0]
        date = date.split(" ")

        # Get rid of useless stuff at beginning
        if date[0] == "Ongoing":
            date.pop(0)
            date.pop(0)

        # Get rid of ampersands
        #for i in range(0, len(date)):
         #   if date[i].find("&"):
          #      thing = date[i].split("&")
           #     date[i] = thing[0]

        # Finishing up with date
        date = " ".join(date[:4])
        date = date.strip()
        date = date.strip(",")

        # Split address away from date/time and find co-ordinates
        address = ", ".join(firstpart)
        latlong = self.geocoder(address)

        # Checking if there's a description
        if working_desc[0].find(":") == -1:
            description = working_desc.pop(0)
        else:
            description = None

        # Splitting everything else
        working_desc = " ".join(working_desc)
        working_desc = re.sub('<b>', '', working_desc)

        desc_dict = dict(item.split('</b>:&nbsp;') for item in working_desc.split(' <br/>'))

        desc_dict["Date"] = date

        try:
            desc_dict["Latitude"] = latlong[1][0]
            desc_dict["Longitude"] = latlong[1][1]
        except TypeError:
            desc_dict["Latitude"] = None
            desc_dict["Longitude"] = None

        desc_dict["Description"] = description

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
                update_interval = (t + 24*3600 - time.time())
                print("* Will check again tomorrow.")
            else:
                # Convert hours into seconds
                update_interval = update_interval*60*60
                print("* Will check again in", update_interval, "hour(s).")

            time.sleep(update_interval)

updater = Updater(THUNDERMAPS_API_KEY, THUNDERMAPS_ACCOUNT_ID)
updater.start()