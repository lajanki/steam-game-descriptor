from flask import (
    abort,
    Flask,
    jsonify,
    render_template,
    request,
)
from src import generate_description, parser, setup_gcs_models



app = Flask(__name__)

# Set the logging level to DEBUG if Flask is in debug mode
if app.debug:
    import logging
    logger = logging.getLogger("main")
    logger.setLevel(logging.DEBUG)


# create DescriptionGenerator in the global namespace to limit
# API calls
generator = generate_description.DescriptionGenerator()


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/_generate")
def generate_game_description():
    """Endpoint for generating a description."""
    # Only respond, if a custom header was set
    if "X-Button-Callback" in request.headers:
        description = generator()
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
	