# Generate a randomized game description with a title and a list of features.

import os.path
import random
import re
import json
import string

import markdown

from src.generator import generator


POS_TAG_FILE = os.path.join("data", "pos_tags.json")
DEVELOPER_FILE = os.path.join("data", "developers.txt")
TAG_FILE = os.path.join("data", "tags.txt")
SEED_FILE = os.path.join("data", "seeds.json")


class DescriptionGenerator():
	"""Generate a formatted game description consisting of
	 * a title
	 * >= 1 main description paragraphs
	 * >= 0 sub sections with titles
	 * >= 0 bullet point list of features
	 * randomly selected tags
	 * developer name
	"""

	def __init__(self):
		"""Load pre-trained generators for description and title."""
		self.markov_generator = generator.Generator("model.pkl")
		self.title_generator = generator.Generator("model_titles.pkl")
		self.feature_generator = generator.Generator("model_features.pkl")
		self.taglines_generator = generator.Generator("model_taglines.pkl")


	def __call__(self):
		"""Generate a description with random number of paragraphs and content types."""
		# Randomize a new content config for each run
		self.config = create_config()

		# Choose a random seed from seeds.txt
		with open(SEED_FILE) as f:
			seeds = json.load(f)

		main_sections = []

		# title 
		size = random.randint(1,4)
		title = self.title_generator.generate(size=size, continue_until_valid=True)
		title = string.capwords(title.rstrip(".")) # use string.capwords to avoid issues with apostrophes
		title = title.replace(".", ":")
		main_sections.append(f"## {title}")

		# tagline
		tagline = ""
		if self.config["tagline"]:
			tagline = self.taglines_generator.generate(size=4, complete_sentence=True)

		# main description
		for _ in range(self.config["paragraphs"]):
			size = int(abs(random.gauss(15, 3.0)))
			seed = random.choice(seeds["text"])
			paragraph = self.markov_generator.generate(seed=seed, size=size, complete_sentence=True)
			main_sections.append(paragraph)
			seed = None

		description = "\n".join(main_sections)
		description_html = markdown.markdown(description)

		# sub sections with headers
		sub_sections = []
		for _ in range(self.config["subsections"]):
			seed = random.choice(seeds["headers"])
			header = self.markov_generator.generate(seed=seed, size=3, continue_until_valid=True)
			header = string.capwords(header.rstrip("."))
			sub_sections.append(f"#### {header}")

			self.markov_generator.ff_to_next_sentence()
			size = int(abs(random.gauss(15, 3.0)))
			paragraph = self.markov_generator.generate(size=size, complete_sentence=True)
			sub_sections.append(paragraph)

		sections_text = "\n".join(sub_sections)
		sections_html = markdown.markdown(sections_text)

		# list of features
		feature_list = []
		for _ in range(self.config["features"]):
			size = min(random.gauss(12, 4), 22) # features should be short
			feature = f" * {self.feature_generator.generate(size=size, complete_sentence=True)}"
			feature_list.append(feature)

		if feature_list:
			feature_list.insert(0, "#### Features")
			features = "\n".join(feature_list)
		else:
			features = ""

		features_html = markdown.markdown(features)

		return {
			"description": description_html,
			"subsections": sections_html,
			"features": features_html,
			"tagline": tagline,
			"tags":	generate_tags(),
			"developer": generate_developer()
		}


def create_config():
	"""Create a randomized config for number of paragraphs and
	types of content to display.
	Content can either be either:
		* main paragraph(s) and a number of subsections with headers, or
		* main paragraph(s) and a list of features
	"""
	# randomly create either features or subsections
	num_of_features = random.randint(2,5) if random.randint(0,1) else 0
	num_of_subsections = random.randint(1,2) if num_of_features == 0 else 0
	return {
		"paragraphs": random.randint(1,2),
		"features": num_of_features,
		"subsections": num_of_subsections,
		"tagline": random.randint(0,1)
	}

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
		tag = tag_template[2:-2]  # tag name within {{ }}

		k = random.randint(1,2)
		new_words = random.sample(pos_map[tag], k)
		template = template.replace(tag_template, " ".join(new_words))

	# return a properly capitalized word
	return template.strip("- ").title()
