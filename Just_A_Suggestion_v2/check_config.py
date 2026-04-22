import google.genai.types as types
print([t for t in dir(types) if 'Image' in t or 'image' in t.lower()])
