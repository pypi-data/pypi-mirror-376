from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="qa-generator",
    version="0.1.0",
    author="QA Generator",
    author_email="",
    description="A Python package to generate question-answer pairs from plain text",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hemanth/qa-generator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "nltk>=3.8",
        "spacy>=3.4.0",
        "transformers>=4.20.0",
        "torch>=1.12.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],
    },
)