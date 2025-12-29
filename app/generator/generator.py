import logging
import random
import pickle

from app import utils


DEFAULT_TEXT_LENGTH = 25
logger = logging.getLogger("app")


class Generator:
	"""A Generator creates text based on a pre-trained Markov model."""

	def __init__(self, model_data, name=None):
		"""Initialize the Generator with model data.

		Args:
			model_data (bytes): A pickle serialized pre-trained raw model data.
			name (str): Optional name for the Generator instance.
		"""
		self.model = pickle.loads(model_data)
		self.name = name

		# Set the initial key to start the text generation to a random key in the model
		self._key = random.choice(list(self.model))

	def generate(
		self,
		seed=None,
		size=DEFAULT_TEXT_LENGTH,
		complete_sentence=False,
		continue_until_valid=False,
		context=None,
	):
		"""Generates a string of size words by randomly selecting words from the successor dictionary using the
		previous n-1 words as the key.
		Args:
			seed (str): initial text to start generting from. If None, a random key is chosen from the model data
			size (int): minimum number of words the text should contain.
			complete_sentence (boolean): continue adding words past the specified minimum size until a punctuation
					character or a whitelisted conjunction is encountered.
			continue_until_valid (boolean): continue adding words until a non-blacklisted word is encountered.
			context (str): optional word to use as context for generation; used to look for semantically
				similar words when multiple choices available. 
		Return:
			the generated text
		"""
		# Ensure size is positive
		if size <= 0:
			logger.warning("Cannot create text with length %s, defaulting to %s", size, DEFAULT_TEXT_LENGTH)
			size = DEFAULT_TEXT_LENGTH

		words = []

		# If a seed was provided and it is found in the model, initialize text with it and
		# use the last n-1 (ie. key length) words as the key.
		if seed:
			model_keys = list(self.model.keys())
			seed_tokens = seed.split()
			key_length = len(model_keys[0])
			key = tuple(seed_tokens[-key_length:])

			if key in self.model:
				self._key = key
				words.extend(seed_tokens)

		# Keep generating words until length condition is satisfied
		while len(words) < size:
			word = self.get_word(context)
			words.append(word)

		# To complete a sentence, keep adding words until a we encounter one ending in punctuation or
		# until the next word is a conjunction.
		if complete_sentence:
			while True:
				word = self.get_word()
				words.append(word)

				# break on punctuation
				if word.endswith((".", "!", "?", "...", "…")):
					break

				# for conjunctions, break the sentence by adding punctuation to the previous word and excluding the current word
				if word.lower() in ("and", "for", "but"):
					words.pop()
					words[-1] = words[-1] + "."
					break

		if continue_until_valid:
			word = words[-1]
			while word.lower() in ("as", "a", "is", "of", "or", "the", "and", "under", "over", "your", "with"):
				word = self.get_word()
				words.append(word)

		return self.cleanup(words)

	def get_word(self, context=None):
		"""Choose a random successor word from the model matching the current state key. 
		Updates the state by joining the new word with the tail end of the old key.
		Args:
			context (str): optional word to use as context; used to look for semantically
				similar words when multiple choices available. 
		Return
			a randomly chosen successor
		"""
		try:
			choices = self.model[self._key]
		except KeyError:
			# In rare cases the model may not contain the key.
			# Choose a random key and try again.
			logger.warning("No successor for %s. Model: %s. Choosing a new seed.", self._key, self.name)
			self._key = random.choice(list(self.model))
			choices = self.model[self._key]

		# If there is only one choice, avoid 
		# invoking random unnecessarily.
		if len(choices) == 1:
			next_word = next(iter(choices))
		elif len(choices) > 1 and context:
			next_word = utils.get_closest_word_match(context, choices)
		else:
			next_word = random.choice(list(choices))

		# Update current key: shift to the right once and add the chosen word
		self._key = (*self._key[1:], next_word)

		# If the new key is not in the model, choose a random key.
		# TODO: Find out why this happens.
		if self._key not in self.model:
			logger.warning("Key %s not found in model %s. Choosing a new seed.", self._key, self.name)
			self._key = random.choice(list(self.model))

		return next_word

	def ff_to_next_sentence(self):
		"""Fast forward the model to a 'natural' sentence break. Fetch a new word 
		ignoring the output until the key ends with punctuation.
		Thus, the next word generated corresponds to a sentence break in the training data.
		"""
		while not self._key[-1].endswith((".", "!", "?", "...", "…")):
			self.get_word()

	def cleanup(self, tokens):
		"""cleanup a sentence by capitalizing the first letter, remove certain characters such as
		parenthesis which are difficult to properly handle on random text generation.
		Arg:
			tokens (list): the sentence to normalize as a list of words
		Return:
			the normalized sentence as a string
		"""
		# Ensure the first word is capitalized.
		if tokens[0] != tokens[0].upper():
			tokens[0] = tokens[0].capitalize().strip()

		text = " ".join(tokens)
		replacements = {
			",.": ".",
			" .": ".",
			"(": "",
			")": "",
			"\"": "",
			"“": "",
			"”": "",
			"•": "",
			"●": "",
			"▼": "",
			"■": "",
			"⭐": "",
			"★": "",
			"*": "",
			"®": "",
			"—": ""
		}
		for old, new in replacements.items():
			text = text.replace(old, new)

		text = text.strip(",;:-* ")
		return text
