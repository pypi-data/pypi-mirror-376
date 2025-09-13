import os
from .config_generator import create_skeleton_config
from .anonymizer import load_config, anonymize_text

# Default path: create JSON in the current working directory (user project)
CONFIG_PATH = os.path.join(os.getcwd(), "critical_words.json")

# Ensure skeleton JSON exists on first import
if not os.path.exists(CONFIG_PATH):
    try:
        create_skeleton_config(CONFIG_PATH)
    except Exception as e:
        # Fail silently if creation fails, so import doesn't break
        print(f"[anonymizer_lib] Warning: could not create skeleton config: {e}")

__all__ = ["create_skeleton_config", "load_config", "anonymize_text"]
