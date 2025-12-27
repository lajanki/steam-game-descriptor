# Parses Steam game descriptions, in batches, to temporary Cloud Storage bucket.
# Uses the undocumented store.steampowered.com/api for app descriptions.
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
from datetime import datetime

from bs4 import BeautifulSoup

from app.utils import json_set_encoder, gcs


logger = logging.getLogger("app")

API_ENDPOINT = "https://store.steampowered.com/api/appdetails"


def upload_description_batch(batch_size=200):
	"""Upload a randomly selected batch of Steam game descriptions to the data bucket.
	Args:
		batch_size (int): sample size of descriptions to parse.
	"""
	app_id_batch = get_app_id_batch(batch_size)

	TEMP_BUCKET_PREFIX = os.environ["TEMP_BUCKET_PREFIX"]

	logger.info("Parsing %s descriptions", batch_size)
	with requests.Session() as s:
		s.params = {"cc": "us", "l": "english"}

		success = 0
		for app_id in app_id_batch:
			logger.debug("Querying %s?appids=%s", API_ENDPOINT, app_id)
			r = s.get(API_ENDPOINT, params={"appids": app_id})
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
			ds = datetime.today().strftime("%Y-%m-%d")
			name = data["name"].replace("/", "-") # Replace / to avoid issues with Cloud Storage prefixes
			path = f"{TEMP_BUCKET_PREFIX}/{ds}/{name}.json"
			gcs.upload_to_gcs(
				json.dumps(snapshot, cls=json_set_encoder.SetEncoder),
				gcs.TEMP_BUCKET,
				path,
				content_type="application/json",
			)
			success += 1

	logger.info(
		"Succesfully uploaded %s descriptions to %s/%s",
		success,
		gcs.TEMP_BUCKET,
		TEMP_BUCKET_PREFIX,
	)

def get_app_id_batch(batch_size):
	"""Get a batch of pseudo Steam app ids.
	
	While the official Steamworks API provides an endpoint for available apps,
	we only need a small sample of app ids for training purposes.
	https://partner.steamgames.com/doc/webapi/IStoreService#GetAppList

	The app ids start from 10 and (at the time of writing) reach to over 4 000 000.
	Base game ids appear to end with 0.

	The ids returned are not guaranteed to be valid Steam apps.

	Args:
		batch_size (int): number of items to return
	Return:
		a list of random numeric ids
	"""
	return random.sample(range(10, 4_000_000, 10), batch_size)

def _get_app_id_list():
	"""DEPRECATED
	The referenced API endpoint appears to be deprecated
	https://partner.steamgames.com/doc/webapi/isteamapps#GetAppList

	See get_app_id_batch instead.

	Fetch a list of games on the Steam store.
	Return:
		list of app ids
	"""
	logger.info("Fetching app list from Steam API...")
	r = requests.get("https://api.steampowered.com/ISteamApps/GetAppList/v2")
	app_list = r.json()["applist"]["apps"]
	# excude trailers, soundtracks and demos
	app_ids = [ app["appid"] for app in app_list if
		(not any( [token in app["name"] for token in ("Trailer", "Soundtrack", "OST", "Demo")] )
		and app["appid"] >= 10) 
	]

	return app_ids

def format_data_dict(app_content):
	"""Format a dictionary containing items needed for training data. Gather various keys
	from the source API response.
	"""
	return {
		"detailed_description": _html_string_to_text(app_content["detailed_description"]),
		"requirements": _extract_requirements(app_content),
		"ratings": _extract_content_rating(app_content),
		"metadata": {
			"source": f"{API_ENDPOINT}?appids={app_content['steam_appid']}"
		}
	}

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

def _extract_requirements(app_content):
	"""Extract system requirements from raw API response. Parse the three OS specific
	requirements fields for 'key: value' style requirements into a single dict.
	Args:
		app_content (dict): raw contents of an API app description response.
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
			if app_content[header] == []:
				continue

			soup = BeautifulSoup(app_content[header].get(req_type, ""), "html.parser")
			for li in soup.select("li"):
				if ":" in li.text:
					category = li.text.split(":")[0].rstrip(" *")
					value = li.text.split(":")[1].strip()
					requirements_map[category].add(value)
				else:
					logger.warning("Couldn't parse %s as key: value", li.text)
					continue

	return requirements_map

def _extract_content_rating(app_content):
	"""Extract system requirements from raw API response. Parse the three OS specific
	requirements fields for 'key: value' style requirements into a single dict.
	Args:
		app_content (dict): raw contents of an API app description response.
	Return:
		A dict of hardware category and value. Categories include components like
		OS, Processor, Storage.
	"""
	if not app_content["ratings"]:
		return []

	rating_providers = ("esrb", "pegi", "oflc", "cero", "kgrb")
	ratings = [
		app_content.get("ratings", {}).get(provider, {}).get("descriptors", "").replace("\r\n", " ")
		for provider in rating_providers
	]

	# drop empty strings from providers not present for this app
	return [ r for r in ratings if r ]
