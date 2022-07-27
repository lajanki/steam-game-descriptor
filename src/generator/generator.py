import random
import pickle

from src import utils


class Generator:

	def __init__(self):
		self.model = self.load_model()

		# Set initial model key to a random key of the model
		self.key = random.choice(list(self.model))

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

		# If a seed was provided and it is found in the model, initialize text with it and
		# use the last n-1 (ie. key length) words as the key.
		if seed:
			seed_tokens = seed.split()
			key_length = len(model_keys[0])
			key = tuple(seed_tokens[-key_length:])
			
			if key in self.model:
				self.key = key
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

		# Return a properly capitalized string.
		return self.cleanup(words)

	def get_word(self):
		"""Given a key to the model data, choose a random word successor matching that key
		and generate the next key by joining the new words with the tail end of the input key.
		Return
			(word, key) tuple containing the fetched word and the next key
		"""
		next_word = random.choice(list(self.model[self.key]))

		# Update current key: shift to the right once and the new word
		self.key = (*self.key[1:], next_word)

		return next_word

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

		replacements = [
			#(" ?", "?"),
			#(" !", "!"),
			#(" ,", ","),
			#(" .", "."),
			#(" (", ","),
			#(" (", ","),
			(",.", "."),
			(" .", "."),
			("(", ""),
			(")", ""),
			("\"", ""),
			("“", ""),
			("”", ""),
			("•", ""),
			("●", ""),
			("*", ""),
			("®", ""),
			("—", "")
		]
		for item in replacements:
			text = text.replace(item[0], item[1])

		text = text.strip(",;:-* ")
		return text