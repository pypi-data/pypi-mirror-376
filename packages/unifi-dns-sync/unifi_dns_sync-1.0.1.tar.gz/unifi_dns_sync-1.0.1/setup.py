"""
Setup configuration for unifi-dns-sync
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
try:
    with open(os.path.join(this_directory, 'requirements.txt')) as f:
        requirements = f.read().splitlines()
except FileNotFoundError:
    requirements = [
        "requests>=2.28.0",
        "urllib3>=1.26.0",
    ]

setup(
    name="unifi-dns-sync",
    version="1.0.0",
    author="cswitenky",
    description="Automatically sync DNS A records on Unifi controllers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cswitenky/unifi-dns-sync",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Networking :: DNS",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "unifi-dns-sync=unifi_dns_sync.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
