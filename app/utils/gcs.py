# Helper functions for storing and retrieving data from Google Cloud Storage.

import json
import logging
import os
import random

from google.cloud import storage


logger = logging.getLogger()

MODEL_BUCKET = os.environ["MODEL_BUCKET"]
TEMP_BUCKET = os.environ["TEMP_BUCKET"]
TEMP_BUCKET_PREFIX = os.environ["TEMP_BUCKET_PREFIX"]
IMG_BUCKET = os.environ["IMG_BUCKET"]

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

def download_all_source_files():
    """Download all source files from the temp bucket.

    This will take a while depending on the number of files in the bucket.
    TODO: try concurrent download (to file) with transfer manager:
      https://cloud.google.com/python/docs/reference/storage/latest/google.cloud.storage.transfer_manager
    The API does support batch operations, but not for downloading...
      https://cloud.google.com/storage/docs/batch
    Return:
        a list of dicts loaded from the file contents
    """
    blobs = gcs_client.list_blobs(TEMP_BUCKET, prefix=TEMP_BUCKET_PREFIX)
    results = []

    count = 0
    for blob in blobs:
        count += 1
        data = blob.download_as_bytes().decode("utf8")
        results.append(json.loads(data))
    
    logger.info("Loaded %d files from gs://%s/%s", count, TEMP_BUCKET, TEMP_BUCKET_PREFIX)
    return results

def _download_all_model_files():
    """Download all pre-trained model files from Cloud Storage.

    Returns:
        dict: A dictionary mapping model basenames to model data as bytes.
    """
    logger.info("Loading models from gs://%s/models", MODEL_BUCKET)
    
    blobs = gcs_client.list_blobs(MODEL_BUCKET, prefix="models/", match_glob="**.pkl")
    models = {}

    for blob in blobs:
        data = blob.download_as_bytes()
        model_base_name = blob.name.split("/")[-1]
        models[model_base_name] = data
    
    return models

def list_image_bucket():
    """List all blobs in the image bucket.
    Return:
        a list of blobs
    """
    # Always list the contents from the production bucket
    image_bucket = IMG_BUCKET.replace("dev_", "prod_")
    return list(gcs_client.list_blobs(image_bucket))
