from setuptools import setup, find_packages
import os

# Read the contents of README.md for the long description
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="restrict-logins",
    version="1.0.1",
    author="Harshalkumar Ishi",
    author_email="harshalk1999@gmail.com",
    description="A Django application that restricts concurrent user logins by managing active sessions.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/harshalkumar-ishi/restrict-logins",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: Django :: 3.0",
        "Framework :: Django :: 3.1",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Framework :: Django :: 5.1",
        "Framework :: Django :: 5.2",
    ],
    python_requires=">=3.9",
    install_requires=[
        "Django>=3.0",
    ],
)
