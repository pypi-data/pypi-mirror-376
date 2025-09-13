from setuptools import setup, find_packages

setup(
    name="pyportal",
    version="1.0.0",
    description="Import Python script from any directory or git commit history.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Alan Yue",
    author_email="youremail@example.com",  # required by PyPI
    url="https://github.com/yourusername/pyportal",  # optional but recommended
    license="MIT",  # or your license

    # Automatically find packages, or specify modules if it’s just scripts
    packages=find_packages(),
    py_modules=["pyportal"],  # if it’s just a single .py file

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
