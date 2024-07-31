# Contains a setup function for creating new models and saving them to the remote bucket.
# Useful for manually adding any new models as the Flask app expects all models to be present
# at all times.
#
# To update production buckets run with
# python setup_gcs_models.py --env prod



import argparse
import logging
import os
from importlib import reload

import yaml

from src import parser, utils
from src.generator import trainer


logger = logging.getLogger("main")


def setup():
    """Train new generator models and store in Cloud Storage bucket.
    Existing models will be overwritten.
    """
    logger.info("Creating description model...")
    description_text = utils.download_descriptions_as_text()
    t = trainer.Trainer(description_text, "model.pkl")
    t.run()

    logger.info("Creating title model...")
    names_text = parser.get_app_names()
    t = trainer.Trainer(names_text, "model_titles.pkl", 2)
    t.run()

    logger.info("Creating feature model...")
    feature_text = utils.get_text_file("data/features.txt")
    t = trainer.Trainer(feature_text, "model_features.pkl")
    t.run()

    logger.info("Creating tagline model...")
    taglines_text = utils.get_text_file("data/taglines.txt")
    t = trainer.Trainer(taglines_text, "model_taglines.pkl")
    t.run()

    logger.info("Creating system requirement models:")
    requirements_map = utils.download_requirements()
    for key in requirements_map:
        logger.info("%s", key)
        t = trainer.Trainer(" ".join(requirements_map[key]), f"model_requirements_{key}.pkl")
        t.run()

    logger.info("Models saved in gs://%s", utils.MODEL_BUCKET)
    

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--env", nargs="?", help="environment for storing results")
    args = argparser.parse_args()

    if args.env == "prod":
        logger.info("Using production bucket config!")

        # Load production buckets from the app config
        with open("app.yaml") as f:
            data = yaml.safe_load(f)
            os.environ.update(data["env_variables"])
            
        # Reload module to propagate bucket name changes to helper functions
        reload(utils)

    setup()
