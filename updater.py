#!/usr/bin/env python
# Provides a class to use in a self updating script for RSS feeds.
# Modified from DanielGibbsNZ's updater.py.

import thundermaps
import rss
import time

class Updater:
	def __init__(self, key, account_id, url):
		self.tm_obj = thundermaps.ThunderMaps(key)
		self.feed_obj = rss.Feed(url)
		self.account_id = account_id

	def start (self, update_interval=-1):
		# Try to load the source_ids already posted.
		source_ids = []
		try:
			source_ids_file = open(".source_ids_", "r")
			source_ids = [i.strip() for i in source_ids_file.readlines()]
			source_ids_file.close()
		except Exception as e:
			print("! WARNING: No valid cache file was found. This may cause duplicate reports.")

		# Run until interrupt received.
		print("* Updating...")
		while True:
			# Load the data
			items = self.feed_obj.getFeed()

			# Create reports for the listings.
			reports = []
			for report in items:
				# Add the report to the list of reports if it hasn't already been posted.
				if report["source_id"] not in source_ids:
					reports.append(report)
					source_ids.append(report["source_id"])

			# If there is at least one report, send the reports to Thundermaps.
			if len(reports) > 0:
				print("[%s] Sending %d reports to Thundermaps..." % (time.strftime("%c"), len(reports)))
				# Upload 10 at a time.
				for some_reports in [reports[i:i+10] for i in range(0, len(reports), 10)]:
					self.tm_obj.sendReports(self.account_id, some_reports)
				print("* Done.")

			try:
				source_ids_file = open(".source_ids_", "w")
				for i in source_ids:
					source_ids_file.write("%s\n" % i)
				source_ids_file.close()
			except Exception as e:
				print("! WARNING: Unable to write cache file.")
				print("! If there is an old cache file when this script is next run, it may result in duplicate reports.")

			print("* Update completed.")

			if reports == []:
				print("* No new entries added.")

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