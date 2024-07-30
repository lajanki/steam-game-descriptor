import json
import logging
import os
import os.path

from google.cloud import storage



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
	"""Download all descriptions currently in the temp bucket."""
	blobs = gcs_client.list_blobs(TEMP_BUCKET, prefix=TEMP_BUCKET_PREFIX)
	results = []

	count = 0
	for blob in blobs:
		count += 1
		data_string = blob.download_as_bytes().decode("utf8")
		results.append(json.loads(data_string)["detailed_description"])
	
	logging.info("Loaded %d descriptions from gs://%s/%s", count, TEMP_BUCKET, TEMP_BUCKET_PREFIX)

	return " ".join(results)

def get_text_file(filename):
	"""Get contents from a text file."""
	with open(filename) as f:
		return f.read().strip()