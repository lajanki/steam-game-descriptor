import json

class SetEncoder(json.JSONEncoder):
    """Custom JSON encoder for encoding sets as lists."""
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return super().default(obj)