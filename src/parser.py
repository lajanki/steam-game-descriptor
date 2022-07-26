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


import random
import requests
import logging
import string

from bs4 import BeautifulSoup
from src import utils


REQUEST_WINDOW_LIMIT = 200


def get_descriptions():
	"""Send a single asynch API request for an app description matching the input parameters."""
	app_id_list = get_app_id_list()
	sample = random.sample(app_id_list, REQUEST_WINDOW_LIMIT)
	URL = "https://store.steampowered.com/api/appdetails"

	logging.info("Parsing %s descriptions", REQUEST_WINDOW_LIMIT)
	with requests.Session() as s:
		s.params = {"cc": "us", "l": "english"}

		success = 0
		for app_id in sample:
			r = s.get(URL, params={"appids": app_id})
			r.raise_for_status()

			if not r.json()[str(app_id)]["success"]:
				logging.info("Unsuccesful request, appid: %s, skipping...", app_id)
				continue

			data = r.json()[str(app_id)]["data"]
			if data["type"].lower() not in ("game", "dlc", "demo", "advertising", "mod"):
				logging.info("Excluding type: '%s', appid: %s", data["type"], app_id)
				continue

			# description is likely not in english, if it's not a supported language
			if "english" not in data.get("supported_languages", "english").lower():
				logging.info("English not in supported languages, appid: %s, skipping...", app_id)
				continue

			description = data.get("detailed_description")
			if not description:
				logging.info("No description detected, appid: %s, skipping...", app_id)
				continue

			# description is an html string, parse it as plain text and filter
			# out some words.
			filtered_text = html_description_to_text(description)

			name = data["name"].replace("/", "-") # Replace / to avoid issues with Cloud Storage prefixes
			path = f"steam_game_descriptor/descriptions/{name}.txt"
			utils.upload_to_gcs(filtered_text, utils.TEMP_BUCKET, path)
			success += 1

	logging.info("Succesfully uploaded %s descriptions", success)

def get_app_id_list():
	"""Fetch a list of games on the Steam store and their descriptions."""
	r = requests.get("https://api.steampowered.com/ISteamApps/GetAppList/v2")
	app_list = r.json()["applist"]["apps"]
	# excude trailers, soundtracks and demos
	app_ids = [ app["appid"] for app in app_list if
		(not any( [token in app["name"] for token in ("Trailer", "Soundtrack", "OST", "Demo")] )
		and app["appid"] >= 10) 
	]

	return app_ids

def get_app_names():
	"""Fetch a list of app names as string."""
	r = requests.get("https://api.steampowered.com/ISteamApps/GetAppList/v2")
	app_list = r.json()["applist"]["apps"]
	# Assert at least one ASCII chracter in the name
	names = [ app["name"] for app in app_list if any(c in app["name"] for c in string.ascii_uppercase) ]

	# Return a string suitable for trainer
	return " ".join(names)

def html_description_to_text(description):
	soup = BeautifulSoup(description, "html.parser")
	tokens = [item.text for item in soup.contents if item.text]
	text = " ".join(tokens)

	# remove words containing urls, Twitter handles, etc.
	words = text.split()
	blacklist = ("http://", "https://", "www", "@", "/img", "/list", ".com")
	filtered = [word for word in words if not any(item in word.lower() for item in blacklist)]
	return " ".join(filtered)

def cleanup(description):
	"""Cleanup the description string: remove extra and add missing whitespace around puncutation."""

	# Extra whitespace before punctuation
	replacements = {
		" .": ".",
		" ,": ",",
		" :": ":",
		" !": "!",
		" ?": "?",
		" ;": ";"
	}
	for old, new in replacements.items():
		description = description.replace(old, new)


	# Missing whitespace after punctuation
	for word in description.split():
		if len(word) > 3:
			# period: add missing space after if not an email or url
			for char in (".", ":"):
				if char in word[:-1] and not any([token in word for token in ("@", "http", "...", "www")]):
					new_word = word.replace(char, char + " ")
					description = description.replace(word, new_word)

			# other characters: add the space and strip any extra space at the end
			for char in (",", "!", "?", ";"):
				if char in word[:-1]:
					new_word = word.replace(char, char + " ")
					description = description.replace(word, new_word)

	return description
