from collections import defaultdict
import json
import os.path

import nltk


def create_pos_tag_mapping():
	"""Creating a json mapping of POS tag -> word from the nltk Brown Corpus.
	https://www.nltk.org/book/ch02.html
	Note: this required setting up nltk module with the Brown Corpus data, see
	https://www.nltk.org/install.html
	
	This function is intended to be run manually to re-create the mapping data if needed.
	""" 
	d = defaultdict(set)
	tags = nltk.corpus.brown.tagged_words(tagset="universal") 
	for token in tags:
		if not token[0].startswith("'"):
			d[token[1]].add(token[0])

	# Transform values back to list for json compatibility 
	for tag in d:
		d[tag] = list(d[tag])
		
	with open(os.path.join("app", "data", "pos_tags.json"), "w") as f:
		json.dump(d, f, separators=(",", ":"))
