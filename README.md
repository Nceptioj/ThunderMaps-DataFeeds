Thundermaps-DataFeeds
===================

This repository provides example Python scripts for grabbing entries from an RSS feed and using the [ThunderMaps](http://thundermaps.com/) API to periodically post reports.

The example in the root directory is set up to work with NASA's [SpotTheStation](http://spotthestation.nasa.gov/sightings/xml_files/New_Zealand_None_Wellington.xml) service. There are other examples in the Example folder which may be more relevant.

Dependencies
------------

* The `feedparser` library for Python3 (see below)
* The `requests` library for Python3
* A Thundermaps API key and account ID
* The URL of some RSS or Atom feed to grab from

Feedparser 5.1.3 currently has a bug which will cause issues (in this case it breaks everything) in Python 3. For this reason you should get Feedparser 5.1.2 instead. 

Usage
-----
First set these fields with your details and feed URL:

```python
FEED_URL="http://spotthestation.nasa.gov/sightings/xml_files/New_Zealand_None_Wellington.xml"

THUNDERMAPS_API_KEY="..."
THUNDERMAPS_ACCOUNT_ID="..."
```

The Updater class should require no modification and is called at the bottom of the `updater_example.py`:

```python
updater = Updater(THUNDERMAPS_API_KEY, THUNDERMAPS_ACCOUNT_ID)
updater.start()
```

You can optionally pass the start method an update interval in hours but by default it will update daily. Like this:

```python
updater.start(0.20)
```

### Modifying for your feed

In order to customize it for your feed you will need to modify the `Feed` class. First you will need to assign fields in the `getFeed()` method based on what specific data you need to grab from your feed. Here the main data is extracted and put into variables:

```python
# Extracting fields from the feed data
title = rss_parsed['title']
desc = rss_parsed['description']
guid = rss_parsed['guid']
```

The `title`, `description` and `guid` fields are standard for RSS feeds so this shouldn't require any modification but you might need to grab from more fields. This is easy to do. `rss_parsed` is a dictionary containing the data from the XML file.

The `Feed` class has a static method `splitDesc(desc)` which splits a description grabbed from an RSS feed into a dictionary so that it can be processed easily. For example:

```
Date: Tuesday Jan 14, 2014 <br/>;
Time: 9:19 PM <br/>;
Duration: less than  1 minute <br/>;
Maximum Elevation: 12 <br/>;
Approach: 12 above SSE <br/>;
Departure: 106 above SSE <br/>;
```

gets split into:

```python
{"Date": "Tuesday Jan 14, 2014", "Time": "9:19 PM", "Duration": "less than 1 minute", "Maximum Elevation": "12", "Approach": "12 above SSE", "Departure": "106 above SSE"}
```

This means you can grab fields from within the description and pass them to ThunderMaps. In some cases this isn't necessary and you can just ignore it. In other cases it will require heavy modification. Descriptions can be a pain to deal with but it might help to check out some of the other examples.

In the example it's called like this:

```python
# Splitting the description into a dictionary
desc_dict = self.splitDesc(desc)
```

And then the fields are grabbed from the dictionary and assigned to variables. You will need to modify this:

```
# Extracting fields from description (check field names)
duration = desc_dict["Duration"]
category_name = title[11:]
approach = desc_dict["Approach"]
departure = desc_dict["Departure"]
maximum_elevation = int(desc_dict["Maximum Elevation"][:2])
occured_on = self.makeDateTime(desc_dict)

# Location data
latitude = -41.288
longitude = 174.7772
```

You will need to modify the `getDescription(desc)` method too. It returns the description which is sent to ThunderMaps:

```python
# Returns string of formatted description for ThunderMaps
def getDescription(self):
	description_str = "Travelling from " + self.approach + " to " + self.departure + " for " + self.duration + "."
	return description_str
```

Other methods in the Feed class which may need modification:

* `getDateTime()` which returns the occured_on datetime object. 

NASA's feed posts a big batch of events every few weeks. Rather than sending them all to Thundermaps (including ones into the past and far into the future), the example is currently set to send all the events which are happening today. This functionality can be changed or removed entirely in the following lines:

```python
 # Checks to see if the event happens today and appears over 40 degrees, is visible
if ((occured_on.day == time_now.day) & (maximum_elevation > 40)):
```

### Thundermaps module

The examples all use the Thundermaps module by DanielGibbsNZ. To use it in your own code import it using `import thundermaps` and create an instance of the `ThunderMaps` class using your Thundermaps API key. E.g.

```python
import thundermaps

# Replace ... with the actual values.
THUNDERMAPS_API_KEY = "..."
ACCOUNT_ID = ...

# Get reports for an account.
my_thundermaps = thundermaps.ThunderMaps(THUNDERMAPS_API_KEY)
reports = thundermaps.getReports(ACCOUNT_ID)
```

## Current Usage
These modules are currently used in the following Thundermaps accounts:

* [NASA Space Station Sightings](http://www.thundermaps.com/accounts/gdfgsdfg)
* [Flickr Photos (New Zealand](http://www.thundermaps.com/accounts/flickr-testing)
