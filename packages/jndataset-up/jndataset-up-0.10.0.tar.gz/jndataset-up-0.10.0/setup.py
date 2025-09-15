from setuptools import setup, find_packages

setup(
    name="jndataset-up",
    version="0.10.0",
    packages=find_packages(),
    py_modules=['cli'],
    include_package_data=True,
    install_requires=[
        "tqdm",
        "requests",
        "click",
        "psutil",
        "pytz",
        "filelock"
    ],
    entry_points={
        "console_scripts": [
            "jndataset-up = dataset_up.cli:main",
        ],
    },
    author="",
    description="Dataset Uploader SDK",
    long_description=open("README.md",encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/***/dataset-up",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)