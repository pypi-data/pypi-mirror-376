import os
import re
from setuptools import setup

def get_long_description():
    """Reads the README.md file and handles potential encoding errors."""
    try:
        with open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as f:
            return f.read()
    except Exception:
        return 'A comprehensive utility library for Python'

setup(
    name='PySwissLib',
    version='1.0.1',
    author='Gautham Nair',
    author_email='your.email@example.com', # Use your real email
    description='A comprehensive utility library for Python',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/gauthamnair2005/PySwissLib', # Use your GitHub URL
    py_modules=['pyswisslib'],
    install_requires=[
        'numpy',
        'pandas',
        'matplotlib',
        'seaborn',
        'requests',
        'torch',
        'scikit-learn'
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
    ],
)
