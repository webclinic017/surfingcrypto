from setuptools import setup, find_packages

# read the contents of your README file
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="surfingcrypto",
    version="0.1.1",
    description="Customizable interface to cryptocurrencies.",
    long_description_content_type="text/markdown",
    long_description=long_description,
    url="https://github.com/giocaizzi/surfingcrypto",
    author="giocaizzi",
    author_email="giocaizzi@gmail.com",
    packages=find_packages(include=["surfingcrypto", "surfingcrypto.*"]),
    setup_requires=[],
    tests_require=[],
    install_requires=[
        "matplotlib",
        "mplfinance",
        "numpy",
        "pandas",
        "coinbase",
        "pandas_ta",
        "python_dateutil",
        "pytrends",
        "trendln",
        "cryptocmd",
    ],
    extras_require={"dev": [],},
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        ],
    project_urls={
        "Documentation": "https://giocaizzi.github.io/surfingcrypto/",
        "Bug Reports": "https://github.com/giocaizzi/surfingcrypto/issues",
        "Source": "https://github.com/giocaizzi/surfingcrypto",
     },
)
