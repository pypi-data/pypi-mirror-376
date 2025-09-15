from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="afromessage",
    version="0.1.0",
    author="Yonas Fikadie",
    author_email="your.email@example.com",
    description="Python SDK for AfroMessage API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yonas8989/afromessage-python-sdk",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "requests>=2.25.0",
    ],
    entry_points={
        'console_scripts': [
            'afromessage-demo=examples.basic_usage:main',
        ],
    },
)