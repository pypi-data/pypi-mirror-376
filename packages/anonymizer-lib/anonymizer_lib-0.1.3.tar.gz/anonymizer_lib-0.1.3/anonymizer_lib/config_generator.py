# anonymizer_lib/config_generator.py
import json
import os

def create_skeleton_config(file_path):
    """Create skeleton JSON config if it does not exist."""
    if not os.path.exists(file_path):
        skeleton_config = {
            "mapping": {
                "SensitiveWord": "<AliasPlaceholder>"
            },
            "groups": {
                "Category1": {
                    "items": [
                        "ValueExample1",
                        "ValueExample2"
                    ],
                    "placeholder": "<Category1Placeholder>"
                }
            }
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(skeleton_config, f, indent=2)

        # ✅ remove emoji for Windows compatibility
        print(f"[INFO] Skeleton config file created: {file_path}")
    else:
        print(f"[INFO] Config file already exists: {file_path}")
