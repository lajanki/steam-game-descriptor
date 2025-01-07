# Generate randomized descriptions for demonstration purposes

import json
from app import generate_description


generator = generate_description.DescriptionGenerator()

print(json.dumps(generator(), indent=4))
