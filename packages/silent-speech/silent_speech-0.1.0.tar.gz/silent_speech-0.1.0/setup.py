from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Define requirements directly in setup.py instead of reading from file
requirements = [
    "sounddevice>=0.4.6",
    "pyperclip>=1.8.2", 
    "rich>=13.0.0",
    "numpy>=1.21.0",
    "requests>=2.28.0"
]

setup(
    name="silent-speech",
    version="0.1.0",
    author="Silent Speech Team",
    author_email="info@silentspeech.dev",
    description="Real-time audio visualization and voice-to-text chat interface with Gemini AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/laspencer91/silent-speech",
    project_urls={
        "Bug Reports": "https://github.com/laspencer91/silent-speech/issues",
        "Source": "https://github.com/laspencer91/silent-speech",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "silent-speech=silent_speech.main:cli_main",
        ],
    },
    keywords="speech-to-text, audio, gemini, ai, voice, transcription, terminal, cli",
    include_package_data=True,
    zip_safe=False,
)