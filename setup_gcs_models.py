# Contains a setup function for creating new models and saving them to the remote bucket.
# Useful for manually adding any new models as the Flask app expects all models to be present
# at all times.
#
# To update production buckets run with
# python setup_gcs_models.py --env prod


import logging
import os
from importlib import reload

from src import parser, utils
from src.generator import trainer



logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)


def setup():
    """Train new generator models and store in Cloud Storage bucket.
    Existing models will be overwritten.
    """
    logging.info("Creating a new description model...")
    description_text = utils.download_descriptions_as_text()
    t = trainer.Trainer(description_text, "model.pkl")
    t.run()

    logging.info("Creating a new title model...")
    names_text = parser.get_app_names()
    t = trainer.Trainer(names_text, "model_titles.pkl", 2)
    t.run()

    logging.info("Creating a new feature model...")
    feature_text = utils.get_text_file("data/features.txt")
    t = trainer.Trainer(feature_text, "model_features.pkl")
    t.run()

    logging.info("Creating a new tagline model...")
    taglines_text = utils.get_text_file("data/taglines.txt")
    t = trainer.Trainer(taglines_text, "model_taglines.pkl")
    t.run()

    logging.info("Models saved in gs://%s", utils.MODEL_BUCKET)
    

if __name__ == "__main__":
    setup()
