"""
Setup script for FMStream library
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="fmstream",
    version="1.0.0",
    author="HaoWasabi",
    author_email="truonggiahao24@example.com",
    description="A Python library for scraping FM radio station data from fmstream.org",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fmstream-py/fmstream",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        "beautifulsoup4>=4.9.0",
        "fastapi>=0.68.0",
        "pydantic>=1.8.0",
        "uvicorn>=0.15.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
        ],
        "api": [
            "fastapi>=0.68.0",
            "pydantic>=1.8.0", 
            "uvicorn>=0.15.0",
        ],
    },
)
