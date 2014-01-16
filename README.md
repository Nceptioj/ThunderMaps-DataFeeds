Thundermaps-RSS
===================

This repository provides Python modules for grabbing entries from an RSS feed and using the [ThunderMaps](http://thundermaps.com/) API to post reports, and a module that periodically creates Thundermaps reports for the latest RSS entries.

It's currently set up to work with NASA's [SpotTheStation](http://spotthestation.nasa.gov/sightings/xml_files/New_Zealand_None_Wellington.xml) service but could be easily modified for other feeds.

Dependencies
------------

* The `feedparser` library for Python3.
* The `requests` library for Python3.
* A Thundermaps API key and account ID.
* The URL of some RSS or Atom feed to grab from.

Usage
-----

### RSS module

To use the RSS module, import it into your code using `import rss` and create an instance of the `Feed` class with the URL of your feed as a parameter.

To get a list of entries, you can use the `getFeed()` method:

```python
import rss

# Create object for RSS feed
feed_url = 'http://spotthestation.nasa.gov/sightings/xml_files/New_Zealand_None_Wellington.xml'
feed_obj = rss.Feed(feed_url)

# Load the data
items = feed_obj.getFeed()
```
In order to customize it for your feed you will need to modify the `Entry` class in rss.py. First you will need to assign fields in the `__init__` method:

```python
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
```

You can have as many or as few fields as you want. 

The `Entry` class has a method `splitDesc(desc)` which splits a description grabbed from an RSS feed into a dictionary so that it can be processed easily. For example:

```
Date: Tuesday Jan 14, 2014 <br/>;
Time: 9:19 PM <br/>;
Duration: less than  1 minute <br/>;
Maximum Elevation: 12 <br/>;
Approach: 12 above SSE <br/>;
Departure: 106 above SSE <br/>;
```

...gets split into:

```python
{"Date": "Tuesday Jan 14, 2014", "Time": "9:19 PM", "Duration": "less than 1 minute", "Maximum Elevation": "12", "Approach": "12 above SSE", "Departure": "106 above SSE"}
```

...and then the description string is assembled in the `getDescription()` method:

```python
# Returns string of formatted description for ThunderMaps
def getDescription(self):
	description_str = "Travelling from " + self.approach + " to " + self.departure + " for " + self.duration + "."
	return description_str
```

Other methods in the Entry class which may need modification:

* `getDateTime()` which returns the occured_on datetime object
* `makeReport()` which returns the formatted report for ThunderMaps.

NASA's feed posts a big batch of events every few weeks. Rather than sending them all to Thundermaps (including ones into the past and far into the future), rss.py is currently set to send all the events which are happening today. This functionality can be changed or removed entirely in the following lines:

```python
# Checks to see if the event happens today
    if rss_obj.occured_on.day == self.time_now.day && rss_obj.maximum_elevation > 40:
        # Adds the object to the list of valid entries
        all_entries.append(rss_obj)
```

There are some examples in the Examples folder which may help.

### Thundermaps module

To use the Thundermaps module by DanielGibbsNZ, import it into your code using `import thundermaps` and create an instance of the `ThunderMaps` class using your Thundermaps API key. E.g.

```python
import thundermaps

# Replace ... with the actual values.
THUNDERMAPS_API_KEY = "..."
ACCOUNT_ID = ...

# Get reports for an account.
my_thundermaps = thundermaps.ThunderMaps(THUNDERMAPS_API_KEY)
reports = thundermaps.getReports(ACCOUNT_ID)
```

### Updater module
The updater module combines both the RSS and ThunderMaps module and provides a higher level interface for generating ThunderMaps reports for the latest RSS listings. Using the updater module typically consists of these steps:

* Creating a new instance of `Updater` with a ThunderMaps API key, account_id, URL of RSS feed, and a categories dictionary.
* Starting the updater with the `start()` method. You can optionally set an update_interval in hours. For example `start(1)` would set it to update every hour. By default it will update daily.

An example usage is shown below and contained in the `self_updating_rss.py` file.

```
import updater

# Key, account, categories...
THUNDERMAPS_API_KEY = "your api key"
THUNDERMAPS_ACCOUNT_ID = "your account id"
RSS_FEED_URL = 'http://spotthestation.nasa.gov/sightings/xml_files/New_Zealand_None_Wellington.xml'

# Create updater
rss_updater = updater.Updater(THUNDERMAPS_API_KEY, THUNDERMAPS_ACCOUNT_ID, RSS_FEED_URL)

# Start updating
rss_updater.start()
```

**Important:** The updater module uses `.source_ids_` files to store the id's of updates which have already been posted. If you delete these files then it will post duplicates.


## Current Usage

These modules are currently used in this Thundermaps accounts:

* [NASA Space Station Sightings](http://www.thundermaps.com/accounts/gdfgsdfg)
