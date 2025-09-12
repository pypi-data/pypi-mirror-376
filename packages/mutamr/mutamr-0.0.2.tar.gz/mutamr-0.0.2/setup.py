"""
mutAMR --- A lightweight tool to identify variants for AMR prediction
"""
from sys import exit, version_info
from setuptools import setup, find_packages
from os import environ
import logging
import mutamr


with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="mutamr",
    version="0.0.2",
    description="Variant detection for AMR prediction",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MDU-PHL/mutamr",
    author="Kristy Horan",
    author_email="kristyhoran15@gmail.com",
    maintainer="Kristy Horan",
    maintainer_email="kristyhoran15@gmail.com",
    python_requires=">=3.10, <4",
    packages=find_packages(exclude=["contrib", "docs", "tests"]),
    zip_safe=False,
    install_requires=["pytest"],
    test_suite="nose.collector",
    tests_require=["nose", "pytest","psutil"],
    entry_points={
        "console_scripts": [
            "mutamr=mutamr.mutamr:main",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: Implementation :: CPython",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    package_data={"mutamr": ["references/*","references/Mycobacterium_tuberculosis_h37rv/*"]}
)
