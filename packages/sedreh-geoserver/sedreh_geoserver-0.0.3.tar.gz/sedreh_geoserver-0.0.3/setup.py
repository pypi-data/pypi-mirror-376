from setuptools import setup, find_packages
from os import path

working_directory = path.abspath(path.dirname(__file__))

with open(path.join(working_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='sedreh_geoserver',
    version='0.0.3',
    author='Sedreh-Corporation',
    author_email='sedrehgroup@gmail.com',
    description='geoserver customize for sedreh satellite',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=["requests"],
)