#!/usr/bin/env python

# Designed to fetch timed RSS data from the QLD fire feed. Modify the Entry class to customize it for your feed.
# Author: Fraser Thompson

import feedparser
from datetime import datetime

# Entire RSS feed
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

            # Checks to see if the event happens today
            if rss_obj.occured_on.day == self.time_now.day:
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
        self.georss = map(float, rss_parsed['georss_point'].split()) # Split georss point into two floats
        self.guid = rss_parsed['guid']

        # Splitting the description into a dictionary
        desc_dict = self.splitDesc(self.desc)

        # Extracting fields from description
        self.location = desc_dict["LOCATION"]
        self.category_name = desc_dict["TYPE"]
        self.status = desc_dict["STATUS"]
        self.size = desc_dict["SIZE"]
        self.occured_on = self.makeDateTime(desc_dict['UPDATED'])

        # Location data
        self.latitude = self.georss[0]
        self.longitude = self.georss[1]

    # Returns string of formatted description for the report
    def getDescription(self):
        description_str = self.title + ' - ' + self.status + '\n' + "Size: " + self.size + '\n' + "Location: " + self.location
        return description_str

    # Makes a report for each RSS entry to be used by ThunderMaps.
    def makeReport(self):
        listing = {"occurred_on":self.occured_on.strftime('%d/%m/%Y %I:%M %p'),
                    "latitude": self.latitude,
                    "longitude": self.longitude,
                    "description": self.getDescription(),
                    "category_name":self.category_name + " - NSW Fire Incidents",
                    "source_id":self.guid}
        return listing

    # Whips up an easily comparable datetime object from the Date and Time fields of the RSS entry
    # Gets called by splitDesc.
    @staticmethod
    def makeDateTime(string):
        format_12 = '%d %b %Y %H:%M'
        updated_obj = datetime.strptime(string, format_12)
        return updated_obj

    # Splits the description into a dictionary
    # Gets called when the object is created.
    @staticmethod
    def splitDesc(desc):
        desc = " ".join(desc.split())
        desc_dict = dict(item.split(': ') for item in desc.split('<br />'))
        return desc_dict