from setuptools import setup, find_packages

setup(
    name="sybsc",
    version="0.0.1",
    author="Your Name",
    description="TYBSc OS practical codes (starting with CPU Scheduling)",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.6",
)
