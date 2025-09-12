from setuptools import setup, find_packages

setup(
    name="tensorneflow",
    version="0.1.1",
    packages=find_packages(),
    description="A tensorflow utility library",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/tensorneflow",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "tensorneflow=tensorneflow.__main__:main",
        ],
    },
)