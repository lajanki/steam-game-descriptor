# Helper functions for performing various maintenance tasks.

import argparse
import json
import pickle
import statistics
import sys
import textwrap

from app import (
    utils,
    generate_description,
    setup_gcs_models
)


def show_current_model_stats():
    """Compute statistics for the current description model
    in Cloud Storage.
    """
    filename = "models/description.pkl"
    model_data = utils.download_from_gcs(utils.MODEL_BUCKET, filename)
    model = pickle.loads(model_data)

    degrees = []
    for key in model:
        d = len(model[key])
        degrees.append(d)

    median = statistics.median(degrees)
    units = degrees.count(1) / len(degrees)
    mb_size = sys.getsizeof(model_data) / 10**6

    print(textwrap.dedent(f"""\
            Current description model statistics:
            filepath: {utils.MODEL_BUCKET}/{filename} 
            median degree: {median}
            unit ngram rate: {units:.2f}
            size: {mb_size:.2f}MB""")
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run local maintenance tasks")
    parser.add_argument("--demo", action="store_true", help="Generate a sample game description in json format.")
    parser.add_argument("--get-model-stats", action="store_true", help="Show performance statistics for the current description model.")
    parser.add_argument("--train", action="store_true", help="Train new models and store to bucket.")
    args = parser.parse_args()

    if args.demo:
        generator = generate_description.DescriptionGenerator()
        print(json.dumps(generator(), indent=4))

    elif args.get_model_stats:
        show_current_model_stats()

    elif args.train:
        setup_gcs_models.setup()