import logging
import os
from collections import defaultdict

from app import parser, utils, BASE
from app.generator import trainer


logger = logging.getLogger("app")


def setup():
    """Train new generator models and store in Cloud Storage bucket.
    Existing models will be overwritten.
    """
    logger.info("Downloading source files... ")
    source_data_list = utils.gcs.download_all_source_files()

    logger.info("Creating description model...")
    description_text = " ".join([item["detailed_description"] for item in source_data_list])
    t = trainer.Trainer(description_text, "description.pkl")
    t.run()

    logger.info("Creating character level description model...")
    description_text = " ".join([item["detailed_description"] for item in source_data_list])
    t = trainer.Trainer(description_text, "names.pkl", n=4, character_level=True)
    t.run()

    logger.info("Creating feature model...")
    feature_text = utils.common.get_text_file(os.path.join(BASE, "data", "features.txt"))
    t = trainer.Trainer(feature_text, "feature.pkl")
    t.run()

    logger.info("Creating tagline model...")
    taglines_text = utils.common.get_text_file(os.path.join(BASE, "data", "taglines.txt"))
    t = trainer.Trainer(taglines_text, "tagline.pkl")
    t.run()

    # Train a dedicated model for each system requirement category
    logger.info("Creating system requirement models:")
    extracted_requirement_map = _merge_requirements(source_data_list)
    for key in extracted_requirement_map:
        logger.info(" # %s:", key)
        text_data = " ".join(extracted_requirement_map[key])
        t = trainer.Trainer(text_data, f"requirements_{key.replace(' ', '_')}.pkl")
        t.run()

    logger.info("Creating ratings model...")
    # join individual ratings within a single item
    ratings = [ " ".join(item.get("ratings", [])) for item in source_data_list ]

    # join ratings across all items
    ratings_text = " ".join(ratings)
    t = trainer.Trainer(ratings_text, "ratings.pkl")
    t.run()

    logger.info("Models saved in gs://%s", utils.gcs.DATA_BUCKET)

def _merge_requirements(source_data_list):
    """Merge a list of requirement dicts.
    Args:
        source_data_list(list): list of requirements parsed from list of source description files
    Return:
        single dict with list of values from selected keys
    """
    requirements = ( [item["requirements"] for item in source_data_list if "requirements" in item] )

    # Merge individual items in requirements
    CATEGORIES_TO_EXTRACT = (
        "OS",
        "Processor",
        "Memory",
        "Graphics",
        "DirectX",
        "Storage",
        "Hard Drive",
        "Hard Disk Space",
        "Sound Card",
        "Additional",
        "Additional Notes"
    )

    extracted_requirement_map = defaultdict(list)
    for d in requirements:
        for key, value in d.items():
            if key in CATEGORIES_TO_EXTRACT:
                extracted_requirement_map[key].extend(value)

    # Merge keys denoting the same category
    extracted_requirement_map["Storage"].extend(extracted_requirement_map.pop("Hard Drive", []))
    extracted_requirement_map["Storage"].extend(extracted_requirement_map.pop("Hard Disk Space", []))
    extracted_requirement_map["Additional Notes"].extend(extracted_requirement_map.pop("Additional", []))
    return extracted_requirement_map