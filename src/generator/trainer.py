# Markov text generator Trainer.
# Trains a new model based on descriptions in the data bucket. 

import collections
import statistics
import logging
import pickle

from src import utils



class Trainer():

	def __init__(self, train_text_data, filename, n=3):
		self.n = n
		self.train_text_data = train_text_data
		self.filename = filename
		self.model_data = None

	def run(self):
		"""Train a new model and upload to data bucket."""
		self.train()
		self.compute_statistics()

		model = pickle.dumps(self.model_data)
		utils.upload_to_gcs(model, utils.MODEL_BUCKET, self.filename)

	def train(self):
		"""Train the model given input text. Splits the text into ngrams and store as a dict of (n-1)-gram keys
		and 1-gram successor as values.
		"""
		# map successor words as set to avoid duplicates
		data = collections.defaultdict(set)
		for ngram in self.create_ngrams():
			key = tuple(ngram[:-1])  # convert to tuple for a hashable dictionary key
			data[key].add(ngram[-1])

		self.model_data = data

	def create_ngrams(self):
		"""Generator for creating ngrams from the training data. For instance,
		"What a lovely day" would create the following two 3-grams:
			[What, a, lovely], and
			[a, lovely, day]
		Return:
			a generator yielding the ngrams
		"""
		train_data = self.train_text_data.split()
		if len(train_data) < self.n:
			return

		# Yield each ngram
		for i in range(len(train_data) - (self.n - 1)):
			yield train_data[i: i + self.n]

	def compute_statistics(self):
		"""Compute average number of successors per key in the cache data."""
		degrees = []
		for key in self.model_data:
			d = len(self.model_data[key])
			degrees.append(d)

		median = statistics.median(degrees)
		units = degrees.count(1) / len(degrees)

		logging.info("Model statistics - median degree: %s, unit ngram rate: %.2f", median, units)
