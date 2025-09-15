from setuptools import setup

setup(
    name='domainsetup',  # Lowercase, unique on PyPI
    version='0.0.2',
    py_modules=['domainsetup'],  # Matches your filename
    entry_points={
        'console_scripts': [
            'domainsetup = domainsetup:main',  # CLI command: maps to domainsetup.py:main()
        ],
    },
    author='ssskingsss12',
    author_email='smalls3000i@gmail.com',
    description='Web Enumeration Tool',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
    python_requires='>=3.10',
)
