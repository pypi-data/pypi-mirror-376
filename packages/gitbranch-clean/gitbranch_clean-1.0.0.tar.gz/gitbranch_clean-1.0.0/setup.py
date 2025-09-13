from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gitbranch-clean",
    version="1.0.0",
    author="Justin Kindrix",
    description="Delete merged git branches. That's it.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/gitbranch-clean",
    py_modules=["branch_cleaner"],
    entry_points={
        "console_scripts": [
            "branch-cleaner=branch_cleaner:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)