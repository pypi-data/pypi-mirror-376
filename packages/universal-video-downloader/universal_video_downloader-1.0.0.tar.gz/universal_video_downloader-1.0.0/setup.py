#!/usr/bin/env python3
"""
Setup script for Universal Video Downloader
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="universal-video-downloader",
    version="1.0.0",
    author="Aarif5856",
    author_email="aarif@example.com",
    description="Download videos and audio from YouTube, TikTok, Instagram, and more",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Aarif5856/UniversalVideoDownloader",
    project_urls={
        "Bug Tracker": "https://github.com/Aarif5856/UniversalVideoDownloader/issues",
        "Repository": "https://github.com/Aarif5856/UniversalVideoDownloader",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Video",
    ],
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "uvd=universal_video_downloader.cli:main",
            "uvd-gui=universal_video_downloader.gui:main",
            "universal-video-downloader=universal_video_downloader.gui:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)