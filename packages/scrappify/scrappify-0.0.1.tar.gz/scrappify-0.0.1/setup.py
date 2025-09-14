from setuptools import setup, find_packages

setup(
    name="scrappify",
    version="0.0.1",
    packages=find_packages(),
    install_requires=[
        "requests",
        "beautifulsoup4"
    ],
    entry_points={
        'console_scripts': [
            'scrappify=scrappify.cli:main',
        ],
    },
    author="hackinglab",
    author_email="mrfidal@proton.me",
    description="A powerful web scraping and downloading utility",
    long_description=open('README.md', encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ByteBreach/scrappify",
    project_urls={
        "Bug Tracker": "https://github.com/ByteBreach/scrappify/issues",
        "Documentation": "https://github.com/ByteBreach/scrappify#readme",
        "Source Code": "https://github.com/ByteBreach/scrappify",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Utilities",
        "Development Status :: 5 - Production/Stable",
    ],
    keywords=[
        "scraping",
        "web scraping",
        "website downloader",
        "crawler",
        "web crawler",
        "data extraction",
        "regex",
        "hackinglab",
        "mrfidal",
        "email extractor",
        "file downloader",
        "python scraping",
        "automation",
    ],
    python_requires=">=3.6",
)
