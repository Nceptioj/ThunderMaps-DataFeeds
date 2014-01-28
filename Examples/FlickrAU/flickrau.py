#!/usr/bin/env python
'''
Created on 21/01/2014
@author: Fraser Thompson
'''

import flickrapi
import time
import sys
sys.path.append(r"/home/fraser/Thundermaps/ThunderMaps-DataFeeds")
import thundermaps

FLICKR_API_KEY=""
FLICKR_API_SECRET=""

THUNDERMAPS_API_KEY=""
THUNDERMAPS_ACCOUNT_ID="flickr-photos-australia"

class Flickr:
    def __init__(self, FLICKR_API_KEY, FLICKR_API_SECRET):
        self.FLICKR_API_KEY = FLICKR_API_KEY
        self.FLICKR_API_SECRET = FLICKR_API_SECRET
        self.num_found = 0

    # Assembles the description to be attached to each report
    def getDescription(self):
        desc_lst = []
        #Description
        desc_lst.append("'"+ self.title + "'" + " by "  + "<a href=\"" + self.owner_url + "\">" + self.owner + "</a> at " + self.location + ".</br>")
        #Image
        desc_lst.append("<a href=\"" + self.image_url + "\"><br><img title=\"Click for larger view\" src=\"" + self.thumb_url + "\" alt=\"Click for larger view\"></a></br>")
        desc_str = "</br>".join(desc_lst)
        return desc_str


    def format_feed(self):
        flickr = flickrapi.FlickrAPI(FLICKR_API_KEY, FLICKR_API_SECRET, format='parsed-json')

        # For finding the ID of a new place to use in the search method. Replace query with place you want.
        #print(flickr.places.find(query = "Australia"))

        # Return safe photos taken in last two hours in Australia
        photos = flickr.photos.search(min_upload_date=int(time.time()-3600), min_taken_date=int(int(time.time()-3600)), accuracy=16, has_geo=1,
                                      safe_search="safe_search", per_page='10', content_type=1, place_id="3fHNxEZTUb4mc08chA")
        try:
            photos_lst = photos['photos']['photo']
            self.num_found = len(photos_lst)
        except KeyError:
            print("No photos available! Did you put in your Flickr and ThunderMaps API keys?")
            pass


        listings = []

        for i in range(0, self.num_found):
            self.title = photos_lst[i]['title']
            photo_id = photos_lst[i]['id']
            secret = photos_lst[i]['secret']

            # Photo information
            photo_info = flickr.photos.getInfo(photo_id=photo_id, secret=secret, extras="original_format")
            server_id = str(photo_info["photo"]["server"])
            farm_id = str(photo_info["photo"]["farm"])
            date = str(photo_info["photo"]["dates"]["taken"])
            nsid = str(photo_info["photo"]["owner"]["nsid"])
            ext = photo_info["photo"].get("originalformat", "jpg")
            self.owner = photo_info["photo"]["owner"]["username"]
            self.image_url = photo_info["photo"]["urls"]["url"][0]["_content"]

            # Location information
            lat = float(photo_info["photo"]["location"]["latitude"])
            long = float(photo_info["photo"]["location"]["longitude"])
            neighbourhood = "Somewhere"
            if "neighbourhood" in photo_info["photo"]["location"]:
                neighbourhood = photo_info["photo"]["location"]["neighbourhood"]["_content"]
            region  = photo_info["photo"]["location"]["region"]["_content"]
            self.location = neighbourhood + ", " + region

            # URLs
            self.url = "http://farm" + farm_id + ".staticflickr.com/" + server_id + "/" + photo_id + "_" + secret + "." + ext
            self.thumb_url = "http://farm" + farm_id + ".staticflickr.com/" + server_id + "/" + photo_id + "_" + secret + "_n." + ext
            self.owner_url = flickr.urls.getUserProfile(user_id=nsid)["user"]["url"]

            listing = {"occurred_on":date,
                       "latitude":lat,
                       "longitude":long,
                       "description": self.getDescription(),
                       "category_name":"Flickr Photos (AUS)",
                       "source_id":self.url,
                       "attachment_url": self.url}

            #create a list of dictionaries
            listings.insert(0, listing)
        return listings

class Updater:
    def __init__(self, key, account_id):
        self.tm_obj = thundermaps.ThunderMaps(key)
        self.feed_obj = Flickr(FLICKR_API_KEY, FLICKR_API_SECRET)
        self.account_id = account_id

    def start(self, update_interval=-1):
        # Try to load the source_ids already posted.
        source_ids = []
        try:
            source_ids_file = open(".source_ids_flickrau", "r")
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
                source_ids_file = open(".source_ids_flickrau", "w")
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