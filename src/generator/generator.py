import random
import pickle

from src import utils


class Generator:

	def __init__(self):
		self.model = self.load_model()

		# Set initial model key to a random key of the model
		self._key = random.choice(list(self.model))

	def load_model(self):
		model_data = utils.download_from_gcs(utils.MODEL_BUCKET, "model.pkl")
		return pickle.loads(model_data)

	def generate(self, seed=None, size=25, complete_sentence=False, continue_until_valid=False):
		"""Generates a string of size words by randomly selecting words from the successor dictionary using the
		previous n-1 words as the key.
		Arg:
			seed (str): initial text to start generting from. If None, a random key is chosen from the model data
			size (int): minimum number of words the text should contain.
			complete_sentence (boolean): continue adding words past minimum size until a punctuation
				character or a whitelisted conjunction is encountered.
			continue_until_valid (boolean): continue adding words until a non-blacklisted word is encountered.
		Return:
			the generated text
		"""
		words = []
		model_keys = list(self.model.keys())

		# If a seed was provided and it is found in the model, initialize text with it and
		# use the last n-1 (ie. key length) words as the key.
		if seed:
			seed_tokens = seed.split()
			key_length = len(model_keys[0])
			key = tuple(seed_tokens[-key_length:])
			
			if key in self.model:
				self._key = key
				words.extend(seed_tokens)

		# Keep generating words until length condition is satisfied
		while len(words) < size:
			word = self.get_word()
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
			while word.lower() in ("as", "a", "is", "of", "the", "and", "under", "over", "your"):
				word = self.get_word()
				words.append(word)

		return self.cleanup(words)

	def get_word(self):
		"""Choose a random successor word from the model matching current key and 
		update the key by joining the new word with the tail end of the old key.
		Return
			a randomly chosen word
		"""
		next_word = random.choice(list(self.model[self._key]))

		# Update current key: shift to the right once and the new word
		self._key = (*self._key[1:], next_word)

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
		# Capitalize and strip the first word (calling capitalize() on the whole string would
		# decapitalize everyting else).
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
			"★": "",
			"*": "",
			"®": "",
			"—": ""
		}
		for old, new in replacements.items():
			text = text.replace(old, new)

		text = text.strip(",;:-* ")
		return text