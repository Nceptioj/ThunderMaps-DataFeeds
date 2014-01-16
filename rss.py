#!/usr/bin/env python

# Designed to fetch timed RSS data from NASA's spot the station feed. Modify the Entry class for other feeds.
# NASA's feed is updated every two weeks with the next two weeks entries so this will check the feed for
# occurances in the next day.
# Author: Fraser Thompson

import feedparser
from datetime import datetime

# Entire Feed
class Feed:
    def __init__(self, rss):
        self.rss = rss

    # Creates a feedparser object for feed, processes it, return list of report dicts for each valid entry.
    def getFeed(self):
        self.rss_parsed = feedparser.parse(self.rss)
        self.time_now = datetime.now()
        all_entries = []

        for i in range(0, self.getLength()):
            rss_obj = Entry(self.rss_parsed['entries'][i])

            # Checks to see if the event happens today and appears over 40 degrees, is visible
            if rss_obj.occured_on.day == self.time_now.day & rss_obj.maximum_elevation > 40:
                # Adds the report to the list of valid entries
                all_entries.append(rss_obj.makeReport())

        return all_entries

    def getLength(self):
        return len(self.rss_parsed['entries'])

# Individual RSS entry
class Entry:
    def __init__(self, rss_parsed):
        # Extracting fields from the feed data
        self.title = rss_parsed['title']
        self.desc = rss_parsed['description']
        self.guid = rss_parsed['guid']

        # Splitting the description into a dictionary
        desc_dict = self.splitDesc(self.desc)

        # Extracting fields from description (check field names)
        self.duration = desc_dict["Duration"]
        self.category_name = self.title[11:]
        self.approach = desc_dict["Approach"]
        self.departure = desc_dict["Departure"]
        self.maximum_elevation = int(desc_dict["Maximum Elevation"][:2])
        self.occured_on = self.makeDateTime(desc_dict)

        # Location data
        self.latitude = -41.288
        self.longitude = 174.7772

    # Returns string of formatted description for ThunderMaps
    def getDescription(self):
        description_str = "Travelling from " + self.approach + " to " + self.departure + " for " + self.duration + "."
        return description_str

    # Makes a report for each RSS entry to be used by ThunderMaps.
    def makeReport(self):
        listing = {"occurred_on":self.occured_on.strftime('%d/%m/%Y %I:%M %p'),
                    "latitude": self.latitude,
                    "longitude": self.longitude,
                    "description": self.getDescription(),
                    "category_name":self.category_name + " - NASA Alert",
                    "source_id":self.guid}
        return listing

    # Whips up an easily comparable datetime object from the Date and Time fields of the RSS entry
    # Gets called by splitDesc.
    @staticmethod
    def makeDateTime(string):
        updated_str = string['Date'] + " " + string['Time']

        # Because NASA formats their times inconsistently...
        format_12 = '%A %b %d, %Y %I:%M %p'
        format_24 = '%A %b %d, %Y %H:%M %p'
        try:
            updated_obj = datetime.strptime(updated_str, format_12)
        except ValueError:
            updated_obj = datetime.strptime(updated_str, format_24)

        return updated_obj

    # Splits the description into a dictionary
    # Gets called when the object is created.
    @staticmethod
    def splitDesc(desc):
        desc = " ".join(desc.split())
        desc_dict = dict(item.split(': ') for item in desc.split(' <br /> '))
        desc_dict["Departure"] = desc_dict["Departure"][:-6] #because of a pesky regex thing, not usually necessary
        return desc_dict