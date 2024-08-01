# Generate randomized descriptions for demonstration purposes

import json
from src import generate_description


generator = generate_description.DescriptionGenerator()

print(json.dumps(generator(), indent=4))
