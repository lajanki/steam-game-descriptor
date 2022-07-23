import argparse
import logging
from flask import Flask, render_template, jsonify, request, abort

from src import generate_description, parser
from src.generator import trainer



app = Flask(__name__)

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
    """Cron only endpoint for training a new model."""
    # Only respond to cron request from App Engine
    # (The X- headers are stripped by App Engine when they originate from external sources)
    # https://cloud.google.com/appengine/docs/standard/python3/scheduling-jobs-with-cron-yaml#validating_cron_requests
    if "X-Appengine-Cron" in request.headers:
        t = trainer.Trainer()
        t.run()
        return "OK", 200

    abort(500, "Bad request")
    
@app.route("/_parse_descriptions")
def parse_descriptions():
    """Cron only endpoint for parsing a new batch of descriptions."""
    if "X-Appengine-Cron" in request.headers:
        parser.get_descriptions()
        return "OK", 200

    abort(500, "Bad request")
	


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--debug", action="store_true")
    args = argparser.parse_args()

    if args.debug:
        logging.getLogger().setLevel("DEBUG")
        
    app.run(debug=args.debug)