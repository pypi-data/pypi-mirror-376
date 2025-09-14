"""
Setup configuration for Sipho AI package
"""

from setuptools import setup, find_packages
import os
import sys

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "Sipho AI - AI-powered voice command assistant for desktop automation"

# Read requirements from requirements.txt
def read_requirements():
    try:
        with open(os.path.join(this_directory, 'requirements.txt'), encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        return [
            'flask>=2.3.3',
            'flask-cors>=4.0.0', 
            'python-dotenv',
            'openai',
            'pillow',
            'requests'
        ]

# Import custom installation hooks for Windows PATH management
cmdclass = {}
if sys.platform == "win32":
    try:
        from siphoai.setup_hooks import PostInstallCommand, PostDevelopCommand
        cmdclass = {
            'install': PostInstallCommand,
            'develop': PostDevelopCommand,
        }
    except ImportError:
        # Fallback if hooks are not available
        pass

setup(
    name="siphoai",
    version="1.0.2",
    author="NiqueWrld",
    author_email="niquewrld@outlook.com",
    description="AI-powered voice command assistant for desktop automation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/niquewrld/siphoai",  # Update with your GitHub repo
    project_urls={
        "Bug Tracker": "https://github.com/niquewrld/siphoai/issues",
        "Documentation": "https://github.com/niquewrld/siphoai#readme",
        "Source Code": "https://github.com/niquewrld/siphoai",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Desktop Environment",
        "Topic :: Home Automation",
        "Topic :: System :: Systems Administration",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
        ],
        "voice": [
            "SpeechRecognition",
            "pyttsx3",
            "pyaudio",
        ],
    },
    entry_points={
        "console_scripts": [
            "siphoai=siphoai.cli:main",
        ],
    },
    package_data={
        "siphoai": [
            "data/*.json",
            "data/*.txt",
        ],
    },
    include_package_data=True,
    keywords=[
        "voice assistant",
        "desktop automation", 
        "ai assistant",
        "voice commands",
        "home automation",
        "productivity",
        "flask api",
        "openai",
    ],
    zip_safe=False,
    cmdclass=cmdclass,
)