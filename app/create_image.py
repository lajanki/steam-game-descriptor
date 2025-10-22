import base64
from io import BytesIO
import logging
import os
import time
import random
import textwrap

from openai import OpenAI
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from app.utils import gcs, common


logger = logging.getLogger()


def upload_image():
    """Generate a screenshot and upload to Cloud Storage.
    
    Use randomized tags as prompt attributes and as remote
    storage prefix.
    """
    tags = common.select_tags()

    ## Screenshot generation
    logger.info("Generating screenshot image...")
    prompt = textwrap.dedent(f"""
        Create a screenshot for a fictonal {tags.genre} video game described by the following attributes:
        {', '.join(tags.context)}
    """).strip()

    metadata = {
        "genre": tags.genre,
        **{f"tag{i+1}": tag for i, tag in enumerate(tags.context + tags.extra)}
    }

    prefix = f"{tags.genre}/{tags.context[0]}/{int(time.time())}.png"
    gcs.upload_to_gcs(
        _create_image(prompt, metadata),
        gcs.IMG_BUCKET,
        prefix,
        content_type="image/png"
    )
    logger.info("Image uploaded to gs://%s/%s", gcs.IMG_BUCKET, prefix)


    ## Art generation
    logger.info("Generating art image...")
    prompt_style_prefixes = [
        "promotional art",
        "cover art",
        "box art",
    ]
    prompt_suffixes = [
        "Do not add any text to the image",
        "Add generic branding elements but do not add a title",
        "",
    ]

    prompt_prefix = random.choice(prompt_style_prefixes)
    prompt_suffix = random.choice(prompt_suffixes)
    prompt = textwrap.dedent(f"""
        Create a {prompt_prefix} for a fictional {tags.genre} video game described by the following attributes:
        {', '.join(tags.context)}
        {prompt_suffix}.
    """).strip()
    print(prompt)

    prefix = f"{tags.genre}/{tags.context[0]}/art/{int(time.time())}.png"
    gcs.upload_to_gcs(
        _create_image(prompt),
        gcs.IMG_BUCKET,
        prefix,
        content_type="image/png"
    )
    logger.info("Image uploaded to gs://%s/%s", gcs.IMG_BUCKET, prefix)

def _create_image(prompt, metadata={}):
    """Generate an image using OpenAI DALL-E model.
    Args:
        prompt (str): The prompt to use for image generation.
        metadata (dict): A dictionary of metadata to embed in the image.
    Return:
        bytes: The generated image data with embedded metadata.
    """
    client = OpenAI(
        api_key=common.get_openai_secret()
    )

    response = client.images.generate(
        prompt=prompt,
        n=1,
        size="256x256",
        response_format="b64_json"
    )
    image_response_data = response.data[0].b64_json
    image_bytes = base64.b64decode(image_response_data)

    # Create an in-memory file object for manipulating metadata with PIL
    image_fp = BytesIO(image_bytes)
    image = Image.open(image_fp)

    # Add metadata as tags
    img_metadata = PngInfo()
    for key, value in metadata.items():
        img_metadata.add_text(key, value)

    # Create a new file pointer to avoid data corruption issues
    output_image_fp = BytesIO(image_bytes)
    image.save(output_image_fp, format="PNG", pnginfo=img_metadata)

    output_image_fp.seek(0)
    return output_image_fp.getvalue()
