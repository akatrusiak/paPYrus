from setuptools import setup, find_packages

setup(
    name="paPYrus",
    version="0.1.0",
    packages=find_packages(),
    author="Alexander Katrusiak",
    author_email="alexanderkatrusiak@hotmail.com",
    description="A text note searcher and viewer",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    license="LOL",
    url="https://github.com/akatrusiak/paPYrus",
    install_requires=[
        "tkinter",  # add other dependencies if needed
        "nltk",
    ],
    entry_points={
        "console_scripts": [
            "papyrus=paPYrus.gui:main",
        ],
    },
)
