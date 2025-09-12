from setuptools import setup, find_packages
from pathlib import Path

here = Path(__file__).parent
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="imppat-downloader",
    version="1.0.1",
    packages=find_packages(),
    install_requires=[
        "requests",
        "beautifulsoup4",
    ],
    entry_points={
        "console_scripts": [
            "imppat-downloader=imppat_downloader.cli:main",
        ],
    },
    author="Sai Eswar M",
    author_email="msaieswar2002@gmail.com", 
    description="Download all structures from IMPPAT database easily",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 5 - Production/Stable",
    ],
    python_requires=">=3.8",
)
