from setuptools import setup, find_packages

setup(
    name="subprocess-logger",
    version="0.1.0",
    description="Consolidated handler for subprocess logging in Python",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Vi-Nk",
    url="https://github.com/Vi-Nk/subprocess-logger/",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.7",
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="subprocess logging loggers",
    license="MIT License",
    include_package_data=True,
)