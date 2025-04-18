import base64
from io import BytesIO
import logging
import os
import time

from openai import OpenAI
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from app import utils



"""
Create a screenshot for a video game with the following attributes:
 - 6 degrees of freedom
 - flying
 - combat
 - early 2010s
"""

def upload_screenshot():

    # get list of tags
    # generate image
    # upload (to temp bucket?) /img/<genre>/<primary_tag>/<timestamp>.png
    tags = utils.select_tags()
    genre = tags["genre"]
    primary_tag = tags["prompt"][0]
    image_fp = create_image(tags)

    gcs_path = f"img/{genre}/{primary_tag}/{int(time.time())}.png"
    utils.upload_to_gcs(
        image_fp.read(),
        utils.CACHE_BUCKET,
        gcs_path,
        content_type="image/png"
    )
    print(f"Image uploaded to {gcs_path}.")


def create_image(tags):
    """Generate an image using OpenAI DALL-E model.
    Args:
        tags (dict): A wrapper for the various types of image tags
            to use as both prompt inputs and fontend-only display values
            to be stored as metadata.
    """
    client = OpenAI(
        api_key=utils.get_openai_secret()
    )

    prompt = f"""
        Create a screenshot for a {tags['genre']} video game described by the following attributes: 
        {''.join([ ' - ' + t + '\n' for t in tags['context']])}
    """.strip()

    response = client.images.generate(
        prompt=prompt,
        n=1,
        size="256x256",
        response_format="b64_json"
    )
    image_response_data = response.data[0].b64_json
    image_bytes = base64.b64decode(image_response_data)

    # with open("image.png", "wb") as f:
    # 	f.write(image_bytes)

    # Create an in-memory file object for manipulating metadata with PIL
    image_fp = BytesIO(image_bytes)
    image = Image.open(image_fp)

    # Add the tags as custom metadata
    metadata = PngInfo()
    metadata.add_text("genre", tags["genre"])
    for i, tag in enumerate(tags["context"] + tags["extra"]):
        metadata.add_text(f"tag{i+1}", tag)

    # Create a new file pointer to avoid data corruption issues
    output_image_fp = BytesIO(image_bytes)
    image.save(output_image_fp, format="PNG", pnginfo=metadata)

    output_image_fp.seek(0)
    return output_image_fp

