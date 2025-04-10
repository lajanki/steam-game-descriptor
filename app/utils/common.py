# Common utility functions

import random

from google.cloud import secretmanager

from app.utils.data_files import GENRES
from app import nlp


def get_text_file(filename):
    """Get contents from a text file."""
    with open(filename) as f:
        return f.read().strip()
    
def select_tags():
    """Randomly select a group of tags from a static file.
    Tags include:
     * 1 genre tag
     * 1-2 genre dependant tags to be used as context for text and image generation
     * 0-2 additional tags to be used as display only
    Return:
        a dict of the differetn types of tags
    """
    genre, genre_tags = random.choice(list(GENRES["Primary"].items()))

    # initialize tags with the genre and 1 matching primary tag
    wrapper_tags = {
        "genre": genre,
        "context": [random.choice(genre_tags)],
        "extra": []
    }

    # optionally add 1 common context tag for image prompt
    if random.random() <= 0.5:
         wrapper_tags["context"].append(random.choice(GENRES["Common"]))

    # add 0-2 more text-only tags
    r = random.random()
    if r < 0.2:
        return wrapper_tags 

    elif r < 0.72:
        wrapper_tags["extra"].append(random.choice(GENRES["Other"]))

    else:
        wrapper_tags["extra"].extend(random.choices(GENRES["Other"], k=2))

    return wrapper_tags

def get_closest_word_match(context, choices):
    """Find the word in a list of choices that is semantically closest 
    to it.
    Args:
        context (str): the word to find a match for
        choices (list): the list to look for the match
    Return:
        the matching word.
    """
    # Define a custom sort function; set an arbitrary fixed
    # value for short words to save nlp inference delay.
    def _similarity_key(item):
        if len(item) < 4:
            return -5
        return nlp(context).similarity(nlp(item))

    return sorted(choices, key=_similarity_key)[-1]

def get_openai_secret():
    """Fetch OpenAI API key from Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    response = client.access_secret_version(name="projects/webhost-common/secrets/steam-game-descriptor-openai-key/versions/latest")
    return response.payload.data.decode()