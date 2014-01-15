Thundermaps-RSS
===================

This repository provides Python modules for grabbing entries from an RSS feed and using the [ThunderMaps](http://thundermaps.com/) API to post reports, and a module that periodically creates Thundermaps reports for the latest RSS entries.

It's currently set up to work with NASA's [SpotTheStation](http://spotthestation.nasa.gov/sightings/xml_files/New_Zealand_None_Wellington.xml) service but could be easily modified for other feeds.

Dependencies
------------

* The `feedparser` library for Python.
* A Thundermaps API key and account ID.
* The URL of some RSS or Atom feed to grab from.

Usage
-----

### RSS module

To use the RSS module, import it into your code using `import rss` and create an instance of the `Feed` class with the URL of your feed and the update time as parameters. 

To get a list of entries, you can use the `getFeed()` method:

```python
import rss

# Create object for RSS feed
feed_url = 'http://spotthestation.nasa.gov/sightings/xml_files/New_Zealand_None_Wellington.xml' 
feed_obj = rss.Feed(feed_url, last_updated)

# Load the data which happens since data was last retrieved.
items = feed_obj.getFeed()
```

rss.py will have to be modified for each individual feed so that it grabs from the correct fields. The following methods will also need some modification:

* `getDescription()` returns a description string, assembled from various fields
* `getDateTime()` returns the occured_on time/date
* `getCategory()` returns the category name.

NASA's feed posts a big batch of events every few weeks. Rather than sending them all to Thundermaps (including ones into the past and far into the future), rss.py is currently set to send all the events which are happening today. This functionality can be changed or removed entirely in the following lines:

```python
# Checks to see if the event happens today
    if rss_obj.occured_on.day == self.time_now.day:
        # Adds the object to the list of valid entries
        all_entries.append(rss_obj)
```

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

An example usage is shown below.

```
import updater

# Key, account, categories...
THUNDERMAPS_API_KEY = "your api key"
THUNDERMAPS_ACCOUNT_ID = "your account id"
THUNDERMAPS_CATEGORY_ID = {"ISS Sighting": 11870, "CYGNUS Sighting": 11871}
RSS_FEED_URL = 'http://spotthestation.nasa.gov/sightings/xml_files/New_Zealand_None_Wellington.xml'

# Create updater
rss_updater = updater.Updater(THUNDERMAPS_API_KEY, THUNDERMAPS_ACCOUNT_ID, RSS_FEED_URL, THUNDERMAPS_CATEGORY_ID)

# Start updating
rss_updater.start()
```

**Important:** The updater module uses `.source_ids_` files to store the id's of updates which have already been posted. If you delete these files then it will post duplicates.


## Current Usage

These modules are currently used in this Thundermaps accounts:

* [NASA ISS Sightings Wellington](http://www.thundermaps.com/accounts/gdfgsdfg)
