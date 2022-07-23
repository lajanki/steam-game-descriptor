import os.path
import json
from time import time

from google.cloud import storage



ENV = os.getenv("ENV", "dev")
MODEL_BUCKET = f"{ENV}_steam_game_descriptor_data"
TEMP_BUCKET = f"{ENV}_temp_lf345f"

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

def download_descriptions():
	"""Download all descriptions currently in temp bucket."""
	blobs = gcs_client.list_blobs(TEMP_BUCKET, prefix="steam_game_descriptor/descriptions")
	results = []

	for blob in blobs:
		data_string = blob.download_as_bytes().decode("utf8")
		results.append(data_string)
	
	return " ".join(results)
