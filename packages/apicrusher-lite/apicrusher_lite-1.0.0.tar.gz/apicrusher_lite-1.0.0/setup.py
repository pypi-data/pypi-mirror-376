# setup.py
# Path: setup.py
from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="apicrusher-lite",
    version="1.0.0",
    author="APICrusher",
    author_email="hello@apicrusher.com",
    description="Basic AI model router for cost optimization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/apicrusher/apicrusher-lite",
    py_modules=["apicrusher_lite"],  # This is the key change
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        # Only add requests if your code actually uses it
    ],
    keywords="ai api cost optimization routing openai anthropic llm",
)
