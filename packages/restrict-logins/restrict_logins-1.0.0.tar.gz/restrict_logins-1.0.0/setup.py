from setuptools import setup, find_packages
import os

# Read the contents of README.md for the long description
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="restrict-logins",
    version="1.0.0",
    author="Harshalkumar Ishi",
    author_email="harshalk1999@gmail.com",
    description="A Django application that restricts concurrent user logins by managing active sessions.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/harshalkumar-ishi/restrict-logins",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: Django",
    ],
    python_requires=">=3.6",
    install_requires=[
        "Django>=5.2",
    ],
)
