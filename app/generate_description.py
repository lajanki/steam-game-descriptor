# Generate a randomized game description with a title and a list of features.

import dataclasses
import logging
import random
import re
import string
from types import SimpleNamespace

from app import model_specs
from app.generator import generator
from app.utils import gcs, common, data_files


logger = logging.getLogger()


screenshot_pool = None


class DescriptionGenerator():
	"""Generate a formatted game description consisting of
	 * a title
	 * >= 1 main description paragraphs
	 * >= 0 sub sections with titles
	 * >= 0 bullet point list of features
	 * randomly selected tags
	 * developer name
	"""

	def __init__(self, config):
		"""Create generators for each description component.
		Model content is expected to be available in Cloud Storage.
		"""
		self.description_config = None
		model_data = gcs._download_all_model_files()

		# Helper function to create a Generator instance with its identity
		def create_generator(key):
			return generator.Generator(model_data[key + ".pkl"], name=key)

		self.generators = SimpleNamespace(
			description=create_generator("description"),
			title=create_generator("title"),
			feature=create_generator("feature"),
			tagline=create_generator("tagline"),

			system_requirements=SimpleNamespace(
				os=create_generator("requirements_OS"),
				processor=create_generator("requirements_Processor"),
				memory=create_generator("requirements_Memory"),
				graphics=create_generator("requirements_Graphics"),
				storage=create_generator("requirements_Storage"),
				sound_card=create_generator("requirements_Sound_Card"),
				additional_notes=create_generator("requirements_Additional_Notes")
			)
		)

		self.ENABLE_SEMANTIC_CONTEXT = config.get("ENABLE_SEMANTIC_CONTEXT", False)
		if self.ENABLE_SEMANTIC_CONTEXT:
			logger.info("Semantic context enabled for description generation.")

	def __call__(self):
		"""Generate a description with random number of paragraphs and content types."""
		# Randomize a new content config for each run
		self.description_config = create_description_config()
		seeds = data_files.SEEDS
		tags = common.select_tags()

		description = []

		# Title
		size = random.randint(1, 4)
		title = self.generators.title.generate(size=size, continue_until_valid=True)

		title = string.capwords(title.rstrip("."))
		title = title.replace(".", ":")

		# Generate n paragraphs as main content
		paragraphs = []
		for _ in range(self.description_config.num_paragraphs):
			size = int(abs(random.gauss(15, 3)))
			seed = random.choice(seeds["text"])

			# Use the genre as context for the description if enabled
			context = tags.genre if self.ENABLE_SEMANTIC_CONTEXT else None
			paragraphs.append(
				self.generators.description.generate(
					seed=seed,
					size=size,
					complete_sentence=True,
					context=context
				)
			)

		description.append({
			"title": title,
			"content": "\n\n".join(paragraphs)
		})

		# Repeat for sub sections if included in the config;
		# 1 paragraph per section
		for _ in range(self.description_config.num_subsections):
			seed = random.choice(seeds["headers"])
			header = self.generators.description.generate(
				seed=seed, size=3, continue_until_valid=True
			)
			header = string.capwords(header.rstrip("."))
			
			self.generators.description.ff_to_next_sentence()
			size = int(abs(random.gauss(15, 3)))
			context = header if self.ENABLE_SEMANTIC_CONTEXT else None

			paragraph = self.generators.description.generate(
				size=size,
				complete_sentence=True,
				context=context
			)

			description.append({
				"title": header,
				"content": paragraph
			})

		# List of features
		features = []
		for _ in range(self.description_config.num_features):
			# set a shorthish upper bound
			size = min(int(abs(random.gauss(12, 4))), 22)
			features.append(
				self.generators.feature.generate(size=size, complete_sentence=True)
			)

		# Tagline
		tagline = ""
		if self.description_config.tagline:
			tagline = self.generators.tagline.generate(size=4, complete_sentence=True)

		# System requirements;
		# use a list to guarentee ordering
		system_requirements = [
			{
				"name": "OS",
				"value": self.generators.system_requirements.os.generate(
					size=abs(random.gauss(4, 2))
				)
			},
			{
				"name": "Processor",
				"value": self.generators.system_requirements.processor.generate(
					size=abs(random.gauss(9, 4))
				)
			},
			{
				"name": "Memory",
				"value": self.generators.system_requirements.memory.generate(
					size=min(abs(random.gauss(5, 4)), 10)
				)
			},
			{
				"name": "Graphics",
				"value": self.generators.system_requirements.graphics.generate(
					size=min(abs(random.gauss(9, 4)), 20)
				)
			},
			{
				"name": "Storage",
				"value": self.generators.system_requirements.storage.generate(
					size=abs(random.gauss(4, 2))
				)
			}
		]

		# add other categories only if specified in the config
		if self.description_config.system_requirements.sound_card:
			system_requirements.append(
				{
					"name": "Sound Card",
					"value": self.generators.system_requirements.sound_card.generate(
						size=abs(random.gauss(4, 2))
					)
				}
			)

		if self.description_config.system_requirements.additional_notes:
			system_requirements.append(
				{
					"name": "Additional Notes",
					"value": self.generators.system_requirements.additional_notes.generate(
						size=abs(random.gauss(9, 4)),
						continue_until_valid=True
					)
				}
			)


		# Screenshot
		global screenshot_pool
		# Lazy load the screenshot pool on first use
		if screenshot_pool is None:
			screenshot_pool = gcs.list_image_bucket()

		matching_full_blobs = [p for p in screenshot_pool if f"{tags.genre}/{tags.context[0]}" in p.name]
		matching_genre_blobs = [p for p in screenshot_pool if f"{tags.genre}/" in p.name]

		if matching_full_blobs:
			logger.info("Found matching screenshots.")
			screenshot_blobs = matching_full_blobs
		elif matching_genre_blobs:
			logger.info("Found matching screenshots for the genre.")
			screenshot_blobs = matching_genre_blobs
		else:
			logger.info("No matching screenshots found. Using random screenshot.")
			screenshot_blobs = screenshot_pool

		screenshot = random.choice(screenshot_blobs)

		description_model = model_specs.GameDescription(
			description=description,
			features=features,
			tagline=tagline,
			tags=tags,
			developer=generate_developer(),
			system_requirements=system_requirements,
			screenshot_url=screenshot.public_url
		)

		# return a json serializable dict
		return dataclasses.asdict(description_model)

def create_description_config():
	"""Create a randomized description config for what the generated content
	should include.
	
	Main content should include either:
		* main paragraph(s) and a number of subsections with headers, or
		* main paragraph(s) and a list of features
	
	Optional system requirements include a sound card and additional notes.

	Return:
		a DescriptionConfig instance
	"""
	# randomly determine whether to add a list of features or subsections
	num_features = random.randint(2,5) if random.randint(0,1) else 0
	num_subsections = random.randint(1,2) if num_features == 0 else 0

	return model_specs.DescriptionConfig(
        num_paragraphs=random.randint(1,2),
        num_features=num_features,
        num_subsections=num_subsections,
        tagline=random.randint(0,1),
        system_requirements=model_specs._SystemRequirementsConfig(
            sound_card=random.random() > 0.75,
			additional_notes=random.random() > 0.75
		)
    )

def generate_developer():
	"""Generate a developer name from filling templates in data/developers.txt
	with POS data from the app names files.
	"""
	template = random.choice(data_files.DEVELOPER_TEMPLATES).rstrip()
	pos_map = data_files.POS_MAP

	
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
