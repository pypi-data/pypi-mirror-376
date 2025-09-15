# setup.py
# This file is used for packaging the application.
# The entry_points section is updated to point to the new run script.

from setuptools import setup, find_packages

setup(
    name='hf-extractor',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='A tool to extract Hugging Face model information.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/hf-extractor',  # Replace with your GitHub repo
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
        'pandas',
        'huggingface_hub',
        'requests'
    ],
    entry_points={
        'console_scripts': [
            # The entry point now correctly points to the main function
            # in the run script if you were to create one.
            # For now, it's a standard Flask app run via `flask run` or `python run.py`.
            'hf-extractor=run:app',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
