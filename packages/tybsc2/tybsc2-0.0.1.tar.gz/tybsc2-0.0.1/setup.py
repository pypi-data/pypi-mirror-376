from setuptools import setup, find_packages

setup(
    name="tybsc2",  # 👈 new name
    version="0.0.1",
    author="Bipin Yadav",
    description="TYBSc OS Practical Codes (CPU Scheduling, Paging, Memory Mgmt)",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.6",
)
