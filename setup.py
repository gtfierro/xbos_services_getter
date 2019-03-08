from setuptools import find_packages, setup


# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md')) as f:
    long_description = f.read()

setup(
    name='xbos-services-getter',
    version='0.0.2dev1',
    packages=find_packages(),
    # license='Creative Commons Attribution-Noncommercial-Share Alike license',
    author='Daniel Lengyel',
	author_email='daniel.lengyel@berkeley.edu',
    description="Getter functions for xbos services using Python 3.6.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
    	"pandas == 0.24.0",
    	"pytz == 2018.9",
        "xbos-services-utils3 <= 0.0.10.dev0",
        "grpcio==1.16.1",
        "grpcio-tools==1.16.1",
    ],
)
