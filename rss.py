#!/usr/bin/env python

# Designed to fetch timed RSS data from NASA's spot the station feed but could be modified for other feeds.
# NASA's feed is updated every two weeks with the next two weeks entries so this will check the feed for
# occurances in the next half hour. 
# Author: Fraser Thompson

import feedparser, re
from datetime import datetime, timedelta
from time import strptime

# Individual RSS entry
class Entry:
    def __init__(self, title, desc, guid):
        desc_dict = self.splitDesc(desc)
        self.duration = desc_dict["Duration"]
        self.approach = desc_dict["Approach"]
        self.departure = desc_dict["Departure"]
        self.occured_on = self.makeDateTime(desc_dict)
        self.guid = guid
        self.category_name = title[11:] # Where to get the category name from. In this case it's in the first 11 characters of the title.
        

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
        desc_dict["Departure"] = desc_dict["Departure"][:-7] #because of a pesky regex thing
        return desc_dict

    # Returns string of category name
    def getCategory(self):
        return self.category_name

    # Returns datetime object
    def getDateTime(self):
        return self.occured_on

    # Returns string of formatted description
    def getDescription(self):
        return "Visible for: " + self.duration + ", Arrival: " + self.approach + ", Departure: " + self.departure

    # Returns string of GUID used to check for duplicates
    def getGUID(self):
        return self.guid

# Entire RSS feed
class Feed:
    def __init__(self, rss):
        self.rss = rss

    # Creates a feedparser object for feed, processes it, returns array of rss_objects for each valid entry.
    def getFeed(self):
        self.rss_parsed = feedparser.parse(self.rss)
        self.time_now = datetime.now()
        all_entries = []

        for i in range(0, self.getLength()):
            title = self.rss_parsed['entries'][i]['title']
            desc = self.rss_parsed['entries'][i]['description']
            guid = self.rss_parsed['entries'][i]['guid']
            
            rss_obj = Entry(title, desc, guid)

            # Checks to see if the event happens today
            if rss_obj.occured_on.day == self.time_now.day:
                # Adds the object to the list of valid entries
                all_entries.append(rss_obj)
            
        return all_entries

    def getLength(self):
        return len(self.rss_parsed['entries'])

    def getUpdateTime(self):
        return self.time_now
