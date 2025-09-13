Anonymizer Lib

A Python library to mask sensitive words and values using configurable JSON.

🚀 Installation & First Use
# 1. Uninstall old version if exists
pip uninstall -y anonymizer_lib

# 2. Install your local package
pip install anonymizer-lib

# 3. Trigger JSON creation (runs once per project root)
python -m anonymizer_lib


This will create a critical_words.json in your project root.
You can then update this JSON with your mappings and groups.

⚠️ Important Notes

Do not rename the top-level keys mapping or groups.

Inside groups, the key must always be "items".

These keywords are reserved and required by the library to function correctly.

📝 Sections Explained
mapping

Use this for direct word-to-placeholder replacements.

"mapping": {
  "<Original_Name>": "<Mask_Name>",
  "DatabasePassword": "<SecretKey>"
}

groups

Use this when you have multiple values under one category (like servers, IPs, emails, etc.).
Every item in a category will be replaced by the same placeholder.

Example:

"servers": {
  "items": [
    "Server1",
    "Server2",
    "Server3"
  ],
  "placeholder": "<hostname>"
}

Adding More Categories

You can add as many categories as you need.
Follow the pattern below:

"Category3": {
  "items": [
    "ExampleValue1",
    "ExampleValue2"
  ],
  "placeholder": "<Category3Placeholder>"
},
"Category4": {
  "items": [
    "AnotherValue1",
    "AnotherValue2"
  ],
  "placeholder": "<Category4Placeholder>"
}

✅ Example Usage

Example JSON

{
  "mapping": {
    "Password123": "<KeySecret>"
  },
  "groups": {
    "ips": {
      "items": ["127.0.0.1", "10.0.0.1"],
      "placeholder": "<ipaddress>"
    }
  }
}


Input Sentence

The system uses Password123 on 127.0.0.1


Output Sentence

The system uses <KeySecret> on <ipaddress>