import os
import os.path
import json

from google.cloud import storage



MODEL_BUCKET = os.environ["MODEL_BUCKET"]
TEMP_BUCKET = os.environ["TEMP_BUCKET"]

gcs_client = storage.Client()


def upload_to_gcs(data_str, bucket, path):
	"""Upload String to bucket."""
	bucket = gcs_client.get_bucket(bucket)
	blob = bucket.blob(path)
	blob.upload_from_string(data_str)

def download_from_gcs(bucket, path):
	"""Download a file from bucket."""
	bucket = gcs_client.get_bucket(bucket)
	blob = bucket.get_blob(path)
	return blob.download_as_bytes()

def download_descriptions_as_text():
	"""Download all descriptions currently in temp bucket."""
	blobs = gcs_client.list_blobs(TEMP_BUCKET, prefix="steam_game_descriptor/descriptions")
	results = []

	for blob in blobs:
		data_string = blob.download_as_bytes().decode("utf8")
		results.append(data_string)
	
	return " ".join(results)

def get_text_file(filename):
	"""Get contents from a text file."""
	with open(filename) as f:
		return f.read().strip()