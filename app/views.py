# Flask routes
import random

from flask import (
    abort,
    Flask,
    jsonify,
    render_template,
    request
)

from . import (
    generate_description,
    parser,
    setup_gcs_models,
    create_image
)
from app.utils import gcs



app = Flask(__name__)
app.config.from_prefixed_env()

# Set the logging level to DEBUG if Flask is in debug mode.
# Note that will affect lower level loggers as well, including 
# Cloud Storage logging.
# if app.debug:
#     import logging
#     logger = logging.getLogger()
#     logger.setLevel(logging.DEBUG)


# Initialize global variables for lazy loading
generator = None
screenshot_pool = None


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/_generate")
def generate_game_description():
    """Endpoint for generating a description."""
    # Only respond, if a custom header was set
    if "X-Button-Callback" in request.headers:

        # Instantiate a new generator if one doesn't already exist
        global generator, screenshot_pool
        if generator is None:
            generator = generate_description.DescriptionGenerator(app.config)
            screenshot_pool = gcs.list_image_bucket()

        description = generator()

        # Select a screenshot and add it to the generated description
        screenshot = random.choice(screenshot_pool)
        description["screenshot"] = screenshot.public_url

        return jsonify(description)

    abort(500, "Bad request")

@app.route("/_train")
def train_model():
    """Cron only endpoint for training new description models.
    Existing models in the model bucket will be overwritten.
    """
    # Only respond to cron request from App Engine
    # (The X- headers are stripped by App Engine when they originate from external sources)
    # https://cloud.google.com/appengine/docs/standard/python3/scheduling-jobs-with-cron-yaml#validating_cron_requests
    if "X-Appengine-Cron" in request.headers:
        setup_gcs_models.setup()
        return "OK\n", 200

    abort(500, "Bad request")

@app.route("/_parse_descriptions")
def parse_descriptions():
    """Cron only endpoint for parsing and uploading a new batch of descriptions to the data bucket."""
    if "X-Appengine-Cron" in request.headers:
        batch_size = int(request.args.get("batch_size", 200))
        parser.upload_description_batch(batch_size)
        return "OK\n", 200

    abort(500, "Bad request")

@app.route("/_generate_image")
def generate_image():
    """Generate a screenshot and upload to Cloud Storage bucket."""
    if "X-Appengine-Cron" in request.headers:
        create_image.upload_screenshot()
        return "OK\n", 200

    abort(500, "Bad request")
