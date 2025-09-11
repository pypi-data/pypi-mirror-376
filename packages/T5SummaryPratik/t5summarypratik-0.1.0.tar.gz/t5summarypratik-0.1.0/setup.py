from setuptools import setup, find_packages

setup(
    name="T5SummaryPratik",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "transformers",
        "torch",
        "evaluate",
        "textstat",
        "nltk"
    ],
    description="A complete text summarization pipeline using T5 with evaluation metrics",
    long_description=open("readme.md").read(),
    long_description_content_type="text/markdown",
    author="Pratik",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/T5SummaryPratik",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: General",
    ],
    keywords="text summarization, t5, nlp, machine learning",
    python_requires=">=3.8",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/T5SummaryPratik/issues",
        "Source": "https://github.com/yourusername/T5SummaryPratik",
    },
)

