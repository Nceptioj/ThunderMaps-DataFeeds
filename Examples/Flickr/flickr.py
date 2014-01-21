#!/usr/bin/env python
'''
Created on 21/01/2014
@author: Fraser Thompson
'''

import flickrapi
import time
import thundermaps

FLICKR_API_KEY=""
FLICKR_API_SECRET=""

THUNDERMAPS_API_KEY=""
THUNDERMAPS_ACCOUNT_ID=""

class Flickr:
    def __init__(self, FLICKR_API_KEY, FLICKR_API_SECRET):
        self.FLICKR_API_KEY = FLICKR_API_KEY
        self.FLICKR_API_SECRET = FLICKR_API_SECRET
        self.num_found = 0

    @staticmethod
    def getDescription(title, owner, url, location):
        desc = '"'+ title + '" by ' + owner + " at " + location + ".\n" + url
        return desc


    def format_feed(self):
        flickr = flickrapi.FlickrAPI(FLICKR_API_KEY, FLICKR_API_SECRET, format='parsed-json')
        # Return photos taken in last two hours in NZ
        photos = flickr.photos.search(min_upload_date=int(time.time()-7200), min_taken_date=int(int(time.time()-7200)), accuracy=16, has_geo=1,
                                      safe_search="safe_search", per_page='10', content_type=1, place_id="X_2zAGVTUb5..jhXDw")
        self.num_found = photos['photos']['total']

        photos_lst = photos['photos']['photo']
        listings = []

        for i in range(0, int(self.num_found)):
            title = photos_lst[i]['title']
            photo_id = photos_lst[i]['id']
            secret = photos_lst[i]['secret']

            photo_info = flickr.photos.getInfo(photo_id=photo_id, secret=secret)
            server_id = str(photo_info["photo"]["server"])
            farm_id = str(photo_info["photo"]["farm"])
            date = str(photo_info["photo"]["dates"]["taken"])
            owner = str(photo_info["photo"]["owner"]["username"])
            lat = int(photo_info["photo"]["location"]["latitude"])
            long = int(photo_info["photo"]["location"]["longitude"])
            neighbourhood = photo_info["photo"]["location"]["neighbourhood"]["_content"]
            region  = photo_info["photo"]["location"]["region"]["_content"]
            location = neighbourhood + ", " + region

            url = "http://farm" + farm_id + ".staticflickr.com/" + server_id + "/" + photo_id + "_" + secret + ".jpg"

            listing = {"occurred_on":date,
                       "latitude":lat,
                       "longitude":long,
                       "description": self.getDescription(title, owner, url, location),
                       "category_name":"Flickr Photos (NZ)",
                       "source_id":url}

            #create a list of dictionaries
            listings.append(listing)
        return listings

class Updater:
    def __init__(self, key, account_id):
        self.tm_obj = thundermaps.ThunderMaps(key)
        self.feed_obj = Flickr(FLICKR_API_KEY, FLICKR_API_SECRET)
        self.account_id = account_id

    def start(self):
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
            items = self.feed_obj.format_feed()

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

            # Wait 10 minutes before trying again.
            time.sleep(60 * 10)

updater = Updater(THUNDERMAPS_API_KEY, THUNDERMAPS_ACCOUNT_ID)
updater.start()