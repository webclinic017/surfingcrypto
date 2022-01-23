from setuptools import setup, find_packages

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='surfingcrypto',
    version='0.0.1',
    description="A package to make money with crypto to go surfing",
    long_description_content_type='text/markdown',
    long_description=long_description,
    url='https://github.com/giocaizzi/surfing_crypto',
    author='giocaizzi',
    author_email='giocaizzi@gmail.com',
    packages=find_packages(include=['surfingcrypto', 'surfingcrypto.*']),
    setup_requires=[],
    tests_require=['pytest'],
    install_requires=[],
    extras_require={
        "docs":[
            "sphinx",
            "nbsphinx",
            "myst-parser",
            "sphinx_rtd_theme",
            "docutils==0.16" 
            ],
        "dev":[],
        'test':['pytest',"pytest-cov"],
    },
    classifiers=[
        "Programming Language :: Python :: 3.7",
    ],
    project_urls={
        'Documentation':'',
        'Bug Reports': '',
        'Source': '',
    },
)
