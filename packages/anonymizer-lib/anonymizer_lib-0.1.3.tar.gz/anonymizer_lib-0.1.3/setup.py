from setuptools import setup, find_packages
from setuptools.command.install import install
import os
from anonymizer_lib.config_generator import create_skeleton_config

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

class CustomInstall(install):
    def run(self):
        super().run()
        config_path = os.path.join(os.getcwd(), "critical_words.json")
        if not os.path.exists(config_path):
            print(f"[anonymizer_lib] Creating skeleton config at {config_path}")
            create_skeleton_config(config_path)

setup(
    name="anonymizer_lib",
    version="0.1.3",
    author="Vigneshwar K",
    author_email="k.vigneshwar96@gmail.com",
    description="A simple library for anonymizing sensitive words",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kvigneshwar96-droid/anonymizer_lib.git", 
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.7",
    cmdclass={"install": CustomInstall},
)
