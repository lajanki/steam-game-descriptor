import json
import logging
import os
import os.path

from google.cloud import storage


logger = logging.getLogger("main")

MODEL_BUCKET = os.environ["MODEL_BUCKET"]
TEMP_BUCKET = os.environ["TEMP_BUCKET"]
TEMP_BUCKET_PREFIX = os.environ["TEMP_BUCKET_PREFIX"]

gcs_client = storage.Client()


def upload_to_gcs(data, bucket, path, **kwargs):
	"""Upload string data to bucket."""
	bucket = gcs_client.get_bucket(bucket)
	blob = bucket.blob(path)
	blob.upload_from_string(data, **kwargs)

def download_from_gcs(bucket, path):
	"""Download a file from bucket."""
	bucket = gcs_client.get_bucket(bucket)
	blob = bucket.get_blob(path)
	return blob.download_as_bytes()

def download_descriptions_as_text():
	"""Download all descriptions currently in the temp bucket.
	Return:
		a single concatenated string.
	"""
	blobs = gcs_client.list_blobs(TEMP_BUCKET, prefix=TEMP_BUCKET_PREFIX)
	results = []

	count = 0
	for blob in blobs:
		count += 1
		data = blob.download_as_bytes().decode("utf8")
		results.append(json.loads(data)["detailed_description"])
	
	logger.info("Loaded %d descriptions from gs://%s/%s", count, TEMP_BUCKET, TEMP_BUCKET_PREFIX)

	return " ".join(results)

def download_requirements():
	"""Download system requirements from all items in the temp bucket.
	Return:
		a dict of requirements for a whitelisted set of requirement categories.
	"""
	blobs = gcs_client.list_blobs(TEMP_BUCKET, prefix=TEMP_BUCKET_PREFIX)
	CATEGORIES_TO_EXTRACT = (
		"OS",
		"Processor",
		"Memory",
		"Graphics",
		"DirectX",
		"Storage",
		"Sound Card",
		"Additional Notes"
	)
	results = {k: set() for k in CATEGORIES_TO_EXTRACT}

	count = 0
	for blob in blobs:
		count += 1
		data = blob.download_as_bytes().decode("utf8")

		requirements = json.loads(data)["requirements"]

		# extract unique items from the whitelisted categories
		for key in set(requirements.keys()) & set(CATEGORIES_TO_EXTRACT):
			results[key].update(set(requirements[key]))

	return results

def get_text_file(filename):
	"""Get contents from a text file."""
	with open(filename) as f:
		return f.read().strip()