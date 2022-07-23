import random
import pickle

from src import utils


class Generator:

	def __init__(self):
		self.model = self.load_model()

	def load_model(self):
		model_data = utils.download_from_gcs(utils.MODEL_BUCKET, "model.pkl")
		return pickle.loads(model_data)

	def generate(self, seed=None, size=25, complete_sentence=False):
		"""Generates a string of size words by randomly selecting words from the successor dictionary using the
		previous n-1 words as the key.
		Arg:
			seed (str): initial text to start generting from. If None, a random key is chosen from the model data
			size (int): number of words the text should contain.
			complete_sentence (boolean): whether to continue adding words past size until a punctuation
				character or a capitalized word is encoutered.
		Return:
			the generated text
		"""
		words = []
		model_keys = list(self.model.keys())

		# If a seed was provided, use the last n-1 (ie. key length) words as the key...
		if seed:
			seed_tokens = seed.split()

			# determine key length from the model
			key_length = len(model_keys[0])
			key = tuple(seed_tokens[-key_length:])
			
			if key in self.model:
				# Set seed as initial words
				words.extend(seed_tokens)

		# ...otherwise (or if the seed was invalid) select random key from the model
		if not words:
			key = random.choice(model_keys)

		# Generate words until length is satisfied
		while len(words) < size:
			word, key = self.next_word(key)
			words.append(word)

		# To complete a sentence, keep adding words until a we encounter one ending in punctuation or
		# until the next word is a conjunction.
		if complete_sentence:

			while True:
				word, key = self.next_word(key)
				words.append(word)

				# break on punctuation
				if word.endswith((".", "!", "?", "...", "…")):
					break

				# for conjunctions, add punctuation to the previous word and exclude current word
				if word.lower() in ("and", "for", "but"):
					words.pop()
					words[-1] = words[-1] + "."
					break

		# Return a properly capitalized string.
		return self.cleanup(words)

	def next_word(self, key):
		"""Given a key to the model data, choose a random word successor matching that key
		and generate the next key by joining the new words with the tail end of the input key.
		Args:
			key (tuple): a key in the model for a word to fetch
		Return
			(word, key) tuple containing the fetched word and the next key
		"""
		try:
			next_word = random.choice(list(self.model[key]))

			# Create a new key tuple by flattening the rightmost items and add the new word
			new_key = (*key[1:], next_word)

		# If key is not a valid key in the model, randomly choose a new key and matching successor
		except KeyError:
			model_keys = list(self.model.keys())
			new_key = random.choice(model_keys)
			next_word = random.choice(list(model_keys[new_key]))

		return next_word, new_key

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

		# replacements = [
		# 	(" ?", "?"),
		# 	(" !", "!"),
		# 	(" ,", ","),
		# 	(" .", "."),
		# 	(" (", ","),
		# 	(" (", ","),
		# 	("(", ""),
		# 	(")", ""),
		# 	("\"", ""),
		# 	("“", ""),
		# 	("”", ""),
		# 	("”", ""),
		# 	("•", ""),
		# 	("●", ""),
		# 	("—", ""),
		# 	("…", "...")
		# ]
		# for item in replacements:
		# 	text = text.replace(item[0], item[1])

		text = text.strip(",;:-* ")
		return text