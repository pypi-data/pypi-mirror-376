from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="colortqdm",
    version="0.0.1",
    author="Bálint Csanády",
    python_requires='>3.6',
    author_email="csbalint@protonmail.ch",
    license="MIT",
    description="Augment the tqdm class with the ability to track progress of different categories.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aielte-research/colortqdm.git",
    keywords=
    "tqdm, progressbar, color",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    install_requires=["tqdm==4.67.1"],
)