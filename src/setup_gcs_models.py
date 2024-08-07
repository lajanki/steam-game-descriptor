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
    logger.info("Downloading source files... ")
    source_data_list = utils.download_all_source_files()

    logger.info("Creating description model...")
    description_text = " ".join([item["detailed_description"] for item in source_data_list])

    t = trainer.Trainer(description_text, "description.pkl")
    t.run()

    logger.info("Creating title model...")
    names_text = parser.get_app_names()
    t = trainer.Trainer(names_text, "title.pkl", 2)
    t.run()

    logger.info("Creating feature model...")
    feature_text = utils.get_text_file("data/features.txt")
    t = trainer.Trainer(feature_text, "feature.pkl")
    t.run()

    logger.info("Creating tagline model...")
    taglines_text = utils.get_text_file("data/taglines.txt")
    t = trainer.Trainer(taglines_text, "tagline.pkl")
    t.run()

    # Train a dedicated model for each system requirement category
    logger.info("Creating system requirement models:")
    extracted_requirement_map = utils.merge_requirements(source_data_list)
    for key in extracted_requirement_map:
        logger.info(" # %s:", key)
        text_data = " ".join(extracted_requirement_map[key])
        t = trainer.Trainer(text_data, f"requirements_{key.replace(' ', '_')}.pkl")
        t.run()

    logger.info("Models saved in gs://%s", utils.MODEL_BUCKET)


if __name__ == "__main__":
    setup()
