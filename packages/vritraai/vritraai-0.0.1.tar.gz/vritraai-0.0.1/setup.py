from setuptools import setup, find_packages

setup(
    name="vritraai",
    version="0.0.1",
    author="Alex Butler",
    author_email="contact@vritrasec.com",
    description="Reserved package name for upcoming VritraAI Shell project by VritraSec.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/VritraSecz/vritraai",
    packages=find_packages(),
    py_modules=["main"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "vritraai=main:main",
        ],
    },
)
