# Helper functions for storing and retrieving data from Google Cloud Storage.

import io
import json
import logging
import os
import random

from google.cloud import storage
from google.cloud.storage import transfer_manager


logger = logging.getLogger("app")

DATA_BUCKET = os.environ["DATA_BUCKET"]
TRAINING_DATA_PREFIX = os.environ["TRAINING_DATA_PREFIX"]
MODEL_PREFIX = os.environ["MODEL_PREFIX"]
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
    """Download (serially) all model training source files from the temp bucket.

    This will take a while depending on the number of files in the bucket.
    In practice this has little performance implications as this method
    is only called when re-training the models.

    Return:
        a list of dicts loaded from the file contents
    """
    logger.info("Loading data files from gs://%s/%s", DATA_BUCKET, TRAINING_DATA_PREFIX)

    blobs = gcs_client.list_blobs(DATA_BUCKET, prefix=TRAINING_DATA_PREFIX)
    results = []

    count = 0
    for blob in blobs:
        count += 1
        data = blob.download_as_bytes().decode("utf8")
        results.append(json.loads(data))
    
    logger.info("Loaded %d files", count)
    return results

def _download_all_model_files():
    """Download all pre-trained model files from Cloud Storage.

    Uses the transfer_manager module for better throughput and
    concurrent downloads.

    Returns:
        dict: A dictionary mapping model basenames to model data as bytes.
    """
    logger.info("Loading models from gs://%s/%s", DATA_BUCKET, MODEL_PREFIX)
    
    blobs = list(gcs_client.list_blobs(DATA_BUCKET, prefix=MODEL_PREFIX, match_glob="**.pkl"))
    
    # Prepare blob-file pairs for transfer_manager
    blob_file_pairs = [(blob, io.BytesIO()) for blob in blobs]
    
    # Download all files concurrently
    results = transfer_manager.download_many(
        blob_file_pairs,
        max_workers=8,
        worker_type=transfer_manager.THREAD
    )
    
    models = {}
    for (blob, file_obj), result in zip(blob_file_pairs, results):
        if isinstance(result, Exception):
            logger.error("Failed to download %s: %s", blob.name, result)
            continue
        
        # Read the downloaded data from the BytesIO object
        file_obj.seek(0)
        model_base_name = blob.name.split("/")[-1]
        models[model_base_name] = file_obj.read()
    
    logger.info("Loaded %d model files", len(models))
    return models

def list_image_bucket():
    """List all blobs in the image bucket.
    Return:
        a list of blobs
    """
    # Always list the contents from the production bucket
    image_bucket = IMG_BUCKET.replace("dev_", "prod_")
    logger.info("Loading screenshots from gs://%s", image_bucket)

    return list(gcs_client.list_blobs(image_bucket))
