# Generate a randomized game description with a title and a list of features.

import os.path
import random
import re
from collections import defaultdict

import json

from src.generator import generator


POS_TAG_FILE = os.path.join("data", "pos_tags.json")
DEVELOPER_FILE = os.path.join("data", "developers.txt")
TAG_FILE = os.path.join("data", "tags.txt")
SEED_FILE = os.path.join("data", "seeds.txt")


class DescriptionGenerator():

	def __init__(self):
		self.markov_generator = generator.Generator()

	def __call__(self):
		"""Generate a description with 1-3 paragraphs and 2-5 features."""

		# Choose a random seed from seeds.txt
		with open(SEED_FILE) as f:
			seeds = [line.strip() for line in f]
			seed = random.choice(seeds)

		title = f"<h2>{generate_game_title()}</h2>"
		paragraphs = [title]

		# main description
		for _ in range(random.randint(1,3)):
			size = int(abs(random.gauss(20, 10/4.0)))

			paragraph = self.markov_generator.generate(seed=seed, size=size, complete_sentence=True)
			html = f"<p>{paragraph}</p>"
			paragraphs.append(html)
			seed = None

		description = "".join(paragraphs)


		# list of features
		features = ["<h3>Features</h3>"]
		features.append("<ul>")

		for _ in range(random.randint(2,5)):
			size = random.gauss(12, 4)
			size = min(size, 22) # features should be short

			feature = self.markov_generator.generate(size=size, complete_sentence=True)
			html = f"<li>{feature}</li>"
			features.append(html)

		features.append("</ul>")
		features = "".join(features)

		return {
			"description": description + features,
			"tags":	generate_tags(),
			"developer": generate_developer()
		}


def generate_game_title():
	"""Generate a random title based on a local nltk POS tags map file.
	A valid title:
	  * does not start with a particle
	  * does not end with pronoun, determiner or a conjunction
	"""
	title_length = random.randint(1, 3)
	VALID_BASE_TAGS = ('NOUN', 'VERB', 'ADJ', 'DET', 'ADP', 'NUM', 'PRT', 'CONJ', 'PRON', 'ADV')

	if title_length == 1:
		title_tags = [random.choice([tag for tag in VALID_BASE_TAGS if tag not in ("PRON", "DET", "CONJ")])]

	elif title_length == 2:
		title_tags = [random.choice(tag) for tag in 
			[
				[tag for tag in VALID_BASE_TAGS if tag not in ("PRT")],
				[tag for tag in VALID_BASE_TAGS if tag not in ("PRT", "DET", "CONJ")]
			]
		]

	elif title_length == 3:
		title_tags = [random.choice(tag) for tag in 
			[
				[tag for tag in VALID_BASE_TAGS if tag not in ("PRT")],
				VALID_BASE_TAGS,
				[tag for tag in VALID_BASE_TAGS if tag not in ("PRT", "DET", "CONJ")]
			]
		]

	# Fetch matching words from file.
	title = []
	with open(POS_TAG_FILE) as f:
		pos_map = json.load(f)

	for tag in title_tags:
		title.append(random.choice(pos_map[tag]))

	title = " ".join(title) 
	return title.title()

def generate_tags():
	"""Choose 2-5 random game tags from file."""
	with open(TAG_FILE) as f:
		tags = f.readlines()

	# choose number of tags to generate,
	# 1-3 should happen more frequently than 4-6
	r = random.random()
	if r < 0.67: 
		k = random.randint(2,3)
	elif r < 0.9:
		k = random.randint(3,5)
	else:
		k = 5
	
	sample = random.sample(tags, k)
	sample = list(map(str.rstrip, sample))
	return sample

def generate_developer():
	"""Generate a developer name from filling templates in data/developers.txt
	with POS data from the app names files.
	"""
	with open(DEVELOPER_FILE) as f, open(POS_TAG_FILE) as g:
		dev_templates = f.readlines()
		pos_map = json.load(g)

	template = random.choice(dev_templates).rstrip()
	
	# template can be
	#  1. undetermined, such as {{}} Software, where 1-2 nouns and adjectives should be fetched from the POS tag map
	#  2. determined, such as {{NOUN}}ware, where a noun should be fetched
	# Additionally, when preceded by {{?}} add a random tag based on a coin toss
	VALID_TAGS = ["NOUN", "ADJ", "VERB", "ADV"]
	if "{{}}" in template:
		k = random.randint(1,2)
		# select POS tags
		tags = random.choices(VALID_TAGS, k=k) # sample with replacement

		# select 1 word from each tag
		new_words = []
		for tag in tags:
			word = random.choice(pos_map[tag])
			new_words.append(word)

		template = template.replace("{{}}", " ".join(new_words))

	if "{{?}}" in template:
		k = random.randint(0,1)
		tags = random.choices(VALID_TAGS, k=k)

		# if k==0, replace the template {{?}}-string with empty string
		if not tags:
			word = ""
		else:
			word = random.choice(pos_map[tags[0]])

		template = template.replace("{{?}}", word)

	for tag_template in re.findall("{{[A-Z]+}}", template):
		tag = tag_template[2:-2]  # tag name wihtin {{ }}

		k = random.randint(1,2)
		new_words = random.sample(pos_map[tag], k)
		template = template.replace(tag_template, " ".join(new_words))

	# return a properly capitalized word
	return template.strip("- ").title()

def create_title_file():
	"""Creating a json mapping of POS tag -> word from the nltk Brown Corpus.
	https://www.nltk.org/book/ch02.html
	Note: this required setting up nltk module with the Brown Corpus data, see
	https://www.nltk.org/install.html
	""" 
	import nltk

	d = defaultdict(set) # use a set since there's no need for duplicates
	tags = nltk.corpus.brown.tagged_words(tagset="universal") 
	for token in tags:
		if not token[0].startswith("'"):
			d[token[1]].add(token[0])

	# transform values back to list for dumping 
	for tag in d:
		d[tag] = list(d[tag])
		
	with open(POS_TAG_FILE, "w") as f:
		json.dump(d, f, separators=(',', ':'))
