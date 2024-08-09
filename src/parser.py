# Parses Steam game descriptions, in batches, to temporary Cloud Storage bucket.
# Uses both the official Steamworks API api.steampowered.com for fetching available app list
# and the undocumented store.steampowered.com/api for actual descriptions.
# See https://wiki.teamfortress.com/wiki/User:RJackson/StorefrontAPI
# for community wiki on store.steampowered.com usage.
#
# The Steam database contains >73 000 game titles. Rather than parsing all of them, only a small sample
# is stored in the bucket at any one time.
#
# According to the community wiki:
# If you request information about more than 1 appid, you'll need to set filters parameter to value "price_overview,"
# otherwise the server will respond with a "null" and the status code 400 Bad Request.
# If you use multiple appids and try to use multiple filters or any other filter, the server will respond with null.
# This might be a bug from steam's server side.
#
# The API is rate limited (possibly 200 requests per 5 minute window?)
# https://www.reddit.com/r/Steam/comments/304dft/steam_store_api_is_there_a_throttling_limit_on/


import json
import logging
import os
import random
import requests
import string
from collections import defaultdict

from bs4 import BeautifulSoup

from src import utils, json_set_encoder


logger = logging.getLogger("main")

URL = "https://store.steampowered.com/api/appdetails"


def upload_description_batch(batch_size=200):
	"""Upload a randomly selected batch of Steam game descriptions to the data bucket.
	Args:
		batch_size (int): sample size of descriptions to parse.
	"""
	app_id_list = _get_app_id_list()
	sample = random.sample(app_id_list, batch_size)
	TEMP_BUCKET_PREFIX = os.environ["TEMP_BUCKET_PREFIX"]

	logger.info("Parsing %s descriptions", batch_size)
	with requests.Session() as s:
		s.params = {"cc": "us", "l": "english"}

		success = 0
		for app_id in sample:
			logger.debug("Querying %s?appids=%s", URL, app_id)
			r = s.get(URL, params={"appids": app_id})
			r.raise_for_status()

			if not r.json()[str(app_id)]["success"]:
				logger.info("Unsuccesful request, appid: %s, skipping...", app_id)
				continue

			data = r.json()[str(app_id)]["data"]
			description = data.get("detailed_description")
			if not description:
				logger.info("No description detected, appid: %s, skipping...", app_id)
				continue

			if data["type"].lower() not in ("game", "dlc", "demo", "advertising", "mod"):
				logger.info("Excluding type: '%s', appid: %s", data["type"], app_id)
				continue

			if "english" not in data.get("supported_languages", "english").lower():
				logger.info("English not in supported languages, appid: %s, skipping...", app_id)
				continue

			# extract selected keys from the response and convert html string descriptions
			# to plain strings. 
			snapshot = format_data_dict(data)

			name = data["name"].replace("/", "-") # Replace / to avoid issues with Cloud Storage prefixes
			path = f"{TEMP_BUCKET_PREFIX}/{name}.json"
			utils.upload_to_gcs(
				json.dumps(snapshot, cls=json_set_encoder.SetEncoder),
				utils.TEMP_BUCKET,
				path,
				content_type="application/json",
			)
			success += 1

	logger.info(
		"Succesfully uploaded %s descriptions to %s/%s",
		success,
		utils.TEMP_BUCKET,
		TEMP_BUCKET_PREFIX,
	)

def _get_app_id_list():
	"""Fetch a list of games on the Steam store.
	Return:
		list of app ids"""
	r = requests.get("https://api.steampowered.com/ISteamApps/GetAppList/v2")
	app_list = r.json()["applist"]["apps"]
	# excude trailers, soundtracks and demos
	app_ids = [ app["appid"] for app in app_list if
		(not any( [token in app["name"] for token in ("Trailer", "Soundtrack", "OST", "Demo")] )
		and app["appid"] >= 10) 
	]

	return app_ids

def get_app_names(batch_size=100_000):
	"""Fetch a sampled list of app names as a single joined string.
	Args:
		batch_size (int): the sample size; number of apps to parse
	Return:
		a joined string of the app names
	"""
	r = requests.get("https://api.steampowered.com/ISteamApps/GetAppList/v2")
	app_list = r.json()["applist"]["apps"]
	# Assert at least one ASCII chracter in the name

	# Filter results:
	# * at least 1 uppercase ASCII character
	# * ignore some test apps
	names = [
		app["name"]
		for app in app_list
		if (
			not app["name"].lower().endswith("playtest")
			and "valvetestapp" not in app["name"].lower()
			and app["name"] not in ("test", "test2", "test3")
			and any(c in app["name"] for c in string.ascii_uppercase)
		)
	]

	sampled = random.sample(names, batch_size)
	return " ".join(sampled)

def _html_string_to_text(html_string):
	"""Convert a html description to a regular text description."""
	soup = BeautifulSoup(html_string, "html.parser")

	# Extract text as a single string.
	# Ignoring paragraphs matching a known header.
	paragraphs = [
		item
		for item in soup.stripped_strings
		if not item.lower().endswith(("story:", "features:", "about the game"))
	]
	text = " ".join(paragraphs)

	# Remove words containing urls, Twitter contact handles, etc.
	words = text.split()
	blacklist = ("http://", "https://", "www", "@", "/img", "/list", ".com", "features")
	filtered = [word for word in words if not any(item in word.lower() for item in blacklist)]
	return " ".join(filtered)

def format_data_dict(snapshot):
	"""Format a dictionary containing items needed for training data. Gather various keys
	from the source API response.
	"""
	return {
		"detailed_description": _html_string_to_text(snapshot["detailed_description"]),
		"requirements": extract_requirements(snapshot),
		"metadata": {
			"source": f"{URL}?appids={snapshot['steam_appid']}"
		}
	}

def extract_requirements(snapshot):
	"""Extract system requirements from raw API response. Parse the three OS specific
	requirements fields for 'key: value' style requirements into a single dict.
	Args:
		snapshot (dict): raw contents of an API app description response.
	Return:
		A dict of hardware category and value. Categories include components like
		OS, Processor, Storage.
	"""
	system_requirement_headers = ("pc_requirements", "mac_requirements", "linux_requirements")

	requirements_map = defaultdict(set)
	# Read both minimum and recommended sections from all three OS headers into a single
	# dictionary.
	for header in system_requirement_headers:
		for req_type in ("minimum", "recommended"):

			# The data type of the top level OS header is either a list if there's no data
			# for this OS, or an object when it's not empty
			if snapshot[header] == []:
				continue

			soup = BeautifulSoup(snapshot[header].get(req_type, ""), "html.parser")
			for li in soup.select("li"):
				if ":" in li.text:
					category = li.text.split(":")[0].rstrip(" *")
					value = li.text.split(":")[1].strip()
					requirements_map[category].add(value)
				else:
					logger.warning("Couldn't parse %s as key: value", li.text)
					continue

	return requirements_map
