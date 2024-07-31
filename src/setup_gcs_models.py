# Contains a setup function for creating new models and saving them to the remote bucket.
# Useful for manually adding any new models as the Flask application expects all models to be present
# at all times.
#
# To update production buckets run with
# dotenv -f .env.prod run python -m src.setup_gcs_models.py 


import logging

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
        logger.info(" # %s:", key)
        text_data = " ".join(requirements_map[key])
        t = trainer.Trainer(text_data, f"model_requirements_{key.replace(' ', '_')}.pkl")
        t.run()

    logger.info("Models saved in gs://%s", utils.MODEL_BUCKET)
    

if __name__ == "__main__":
    setup()
