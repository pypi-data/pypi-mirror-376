from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="voice_of_python",
    version="0.1.0",
    author="Ujjal Bhattacharya",
    author_email="ujjalbhattacharya525@gmail.com",
    description="Offline multilingual voice bot with Vosk ASR and pyttsx3 TTS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/henry-n2/voice_of_python",  # update as needed
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "vosk",
        "langid",
        "pyttsx3",
        "sounddevice",
        "numpy",
        "soundfile"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries",
    ],
)
