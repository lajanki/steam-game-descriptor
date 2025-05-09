import collections
import statistics
import logging
import pickle
import sys

from app.utils import gcs


logger = logging.getLogger()


class Trainer():
	"""Trainer creates ('trains') a Markov text chain model by splitting source text into ngrams
	and keeping track of which n-1 word chains is followed by the remaining word. Trainers are
	stored in Google Cloud Storage bucket for later access.

	A separate Generator instance can then use this to generate new text where every n consecutive
	words appear somewhere in the original source text.

	Args:
		train_text_data (str): The source text to parse as ngrams
		filename (str): name of the model to use when storing in Cloud Storage
		n (int): ngram size; the number of consecutive words to parse the original text
	"""

	def __init__(self, train_text_data, filename, n=3):
		self.n = n
		self.train_text_data = train_text_data
		self.filename = filename
		self.model = None

	def run(self):
		"""Train a new model and upload to data bucket."""
		if len(self.train_text_data) < 100:
			raise RuntimeError("Cannot train a model with source data of length < 100")

		self.train()
		self.compute_statistics()

		model = pickle.dumps(self.model)
		gcs.upload_to_gcs(model, gcs.MODEL_BUCKET, "models/" + self.filename)

	def train(self):
		"""Train the model given input text. Splits the text into ngrams and store as a dict of (n-1)-gram keys
		and 1-gram successor as values.
		"""
		# map successor words as set to avoid duplicates
		data = collections.defaultdict(set)
		for ngram in self.create_ngrams():
			key = tuple(ngram[:-1])  # convert to tuple for a hashable dictionary key
			data[key].add(ngram[-1])

		# Convert back to a regular dictionary to prevent
		# silently adding new keys during lookup.
		self.model = dict(data)

	def create_ngrams(self):
		"""Generator for creating ngrams from the training data. For instance,
		"What a lovely day" would create the following two 3-grams:
			[What, a, lovely], and
			[a, lovely, day]
		Return:
			a generator yielding the ngrams as list of length n
		"""
		train_data = self.train_text_data.split()
		if len(train_data) < self.n:
			raise RuntimeError(f"Not enough words to split; received {len(train_data)}, need {self.n}")

		# Yield each ngram
		for i in range(len(train_data) - (self.n - 1)):
			yield train_data[i: i + self.n]

	def compute_statistics(self):
		"""Compute statistics for a trained model:
		 * the median degree: the median number of successors for keys
		 * unit ngram rate: the % of keys having degree 1
		 * size in megabytes
		"""
		size = len(self.model)
		degrees = [ len(self.model[key]) for key in self.model ]
		median = statistics.median(degrees)
		units = degrees.count(1) / len(degrees)
		empty = degrees.count(0)
		mb_size = sys.getsizeof(self.model) / 10**6

		logger.info("Model statistics: total keys: %d, median degree: %s, unit ngram rate: %.2f, size: %.2fMB", size, median, units, mb_size)
		if empty:
			logging.warning("Detected %d keys wihtout successors", empty)
