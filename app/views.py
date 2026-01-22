import logging

from flask import (
    abort,
    Flask,
    jsonify,
    render_template,
    request
)

from app.utils.verify_oidc import verify_oidc_token
from app import (
    generate_description,
    parser,
    setup_gcs_models,
    create_image
)


app = Flask(__name__)


# Set the logging level to DEBUG if Flask is in debug mode.
if app.debug:
    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG)


# Initialize global variables for lazy loading
generator = None


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/_generate")
def generate_game_description():
    """Endpoint for generating a description."""
    # Only respond, if a custom header was set
    if "X-Button-Callback" in request.headers:

        # Instantiate a new generator if one doesn't already exist
        global generator
        if generator is None:
            generator = generate_description.DescriptionGenerator(app.config)

        description = generator()
        return jsonify(description)

    abort(500, "Bad request")

@app.route("/_train", methods=["POST"])
@verify_oidc_token
def train_model():
    """Train new description models.
    Existing models in the model bucket will be overwritten.

    This is a cron only endpoint. Expectes a valid OIDC token
    from Cloud Scheduler in the Authorization header.
    """
    setup_gcs_models.setup()
    return "OK\n", 200

@app.route("/_parse_descriptions", methods=["POST"])
@verify_oidc_token
def parse_descriptions():
    """Parse and upload a new batch of descriptions to the data bucket."""
    batch_size = int(request.args.get("batch_size", 200))
    parser.upload_description_batch(batch_size)
    return "OK\n", 200

@app.route("/_generate_image", methods=["POST"])
@verify_oidc_token
def generate_image():
    """Generate a screenshot and upload to Cloud Storage bucket."""
    create_image.upload_image()
    return "OK\n", 200
