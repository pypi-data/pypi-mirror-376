import json, re, os
from .config_generator import create_skeleton_config

def load_config(path="critical_words.json"):
    """Load JSON config file, create if missing."""
    if not os.path.exists(path):
        create_skeleton_config(path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def anonymize_text(sentence, config):
    """Replace sensitive words and group items with placeholders (case-insensitive)."""
    
    # Step 1: Replace words from mapping
    for word, placeholder in config.get("mapping", {}).items():
        sentence = re.sub(rf"\b{re.escape(word)}\b", placeholder, sentence, flags=re.IGNORECASE)
    
    # Step 2: Replace words from groups
    for group in config.get("groups", {}).values():
        placeholder = group.get("placeholder", "")
        for item in group.get("items", []):
            sentence = re.sub(rf"\b{re.escape(item)}\b", placeholder, sentence, flags=re.IGNORECASE)
    
    return sentence
