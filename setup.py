from setuptools import setup, find_packages

# read the contents of your README file
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="surfingcrypto",
    version="0.0.3",
    description="A package to make money with crypto to go surfing",
    long_description_content_type="text/markdown",
    long_description=long_description,
    url="https://github.com/giocaizzi/surfing_crypto",
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
        "plotly",
        "python_dateutil",
        "python_telegram_bot",
        "pytrends",
        "trendln",
        "cryptocmd",
    ],
    extras_require={"dev": [],},
    classifiers=["Programming Language :: Python :: 3.7",],
    project_urls={"Documentation": "", "Bug Reports": "", "Source": "",},
)
