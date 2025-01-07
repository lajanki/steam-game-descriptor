import json
import logging
import os
import os.path
import random
from collections import defaultdict

from google.cloud import storage, secretmanager

from app.data_files import GENRES


logger = logging.getLogger()

MODEL_BUCKET = os.environ["MODEL_BUCKET"]
TEMP_BUCKET = os.environ["TEMP_BUCKET"]
TEMP_BUCKET_PREFIX = os.environ["TEMP_BUCKET_PREFIX"]
CACHE_BUCKET = "dev_steam_game_descriptor_cache" # TODO

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

def get_text_file(filename):
    """Get contents from a text file."""
    with open(filename) as f:
        return f.read().strip()
    
def merge_requirements(source_data_list):
    """Merge a list of requirement dicts.
    Args:
        source_data_list(list): list of requirements parsed from list of source description files
    Return:
        single dict with list of values from selected keys
    """
    requirements = ( [item["requirements"] for item in source_data_list if "requirements" in item] )

    # Merge individual items in requirements
    CATEGORIES_TO_EXTRACT = (
        "OS",
        "Processor",
        "Memory",
        "Graphics",
        "DirectX",
        "Storage",
        "Hard Drive",
        "Hard Disk Space",
        "Sound Card",
        "Additional",
        "Additional Notes"
    )

    extracted_requirement_map = defaultdict(list)
    for d in requirements:
        for key, value in d.items():
            if key in CATEGORIES_TO_EXTRACT:
                extracted_requirement_map[key].extend(value)

    # Merge keys denoting the same category
    extracted_requirement_map["Storage"].extend(extracted_requirement_map.pop("Hard Drive", []))
    extracted_requirement_map["Storage"].extend(extracted_requirement_map.pop("Hard Disk Space", []))
    extracted_requirement_map["Additional Notes"].extend(extracted_requirement_map.pop("Additional", []))
    return extracted_requirement_map

def select_tags():
    """Randomly select a group of tags from a static file.
    Tags include:
     * 1 genre tag
     * 1-2 genre dependant tags to be used as image generating prompt
     * 0-2 additional tags to be used as display only
    Return:
        a dict of the differetn types of tags
    """
    genre, genre_tags = random.choice(list(GENRES["Primary"].items()))

    # initialize tags with the genre and 1 matching primary tag
    wrapper_tags = {
        "genre": genre,
        "prompt": [random.choice(genre_tags)],
        "extra": []
    }

    # optionally add 1 common image prompt tag
    if random.random() <= 0.5:
         wrapper_tags["prompt"].append(random.choice(GENRES["Common"]))

    # add 0-2 more text-only tags
    r = random.random()
    if r < 0.2:
        return wrapper_tags 

    elif r < 0.72:
        wrapper_tags["extra"].append(random.choice(GENRES["Other"]))

    else:
        wrapper_tags["extra"].extend(random.choices(GENRES["Other"], k=2))

    return wrapper_tags

def get_openai_secret():
	"""Fetch OpenAI API key from Secret Manager."""
	client = secretmanager.SecretManagerServiceClient()
	response = client.access_secret_version(name="projects/webhost-common/secrets/steam-game-descriptor-openai-key/versions/latest")
	return response.payload.data.decode()