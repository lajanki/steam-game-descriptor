import base64
from io import BytesIO
import logging
import os
import time

from openai import OpenAI
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from app.utils import gcs, common


def upload_image():
    """Generate a screenshot and upload to Cloud Storage.
    
    Use randomized tags as prompt attributes and as remote
    storage prefix.
    """
    tags = common.select_tags()

    prompt = f"""
        Create a screenshot for a {tags.genre} video game described by the following attributes: 
        {', '.join(tags.context)}
    """.strip()

    metadata = {
        "genre": tags.genre,
        **{f"tag{i+1}": tag for i, tag in enumerate(tags.context + tags.extra)}
    }

    image_bytes = _create_image(prompt, metadata)

    prefix = f"{tags.genre}/{tags.context[0]}/{int(time.time())}.png"
    gcs.upload_to_gcs(
        image_bytes,
        gcs.IMG_BUCKET,
        prefix,
        content_type="image/png"
    )
    print(f"Image uploaded to gs://{gcs.IMG_BUCKET}/{prefix}.")

def _create_image(prompt, metadata):
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
