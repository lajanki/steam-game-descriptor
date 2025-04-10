import pickle
import statistics
import sys
import textwrap

from app.utils import gcs


def show_current_model_stats():
    """Compute statistics for the current description model
    in Cloud Storage.
    """
    filename = "models/description.pkl"
    model_data = gcs.download_from_gcs(gcs.MODEL_BUCKET, filename)
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
            filepath: {gcs.MODEL_BUCKET}/{filename} 
            median degree: {median}
            unit ngram rate: {units:.2f}
            size: {mb_size:.2f}MB""")
    )