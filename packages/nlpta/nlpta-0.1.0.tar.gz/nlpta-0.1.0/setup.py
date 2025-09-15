from setuptools import setup, find_packages

setup(
    name="nlpta",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "beautifulsoup4",
        "gensim",
        "pytest"
    ],
    author="Fuad Sadik",
    author_email="fuadsadik21@gmail.com",
    description="NLP Toolkit for Amharic",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/fuadsadik21/nlpta",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    include_package_data=True,
    package_data={
        "nlpta": ["../data/*"],
    },
)