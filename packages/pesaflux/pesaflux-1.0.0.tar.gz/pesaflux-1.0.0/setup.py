from setuptools import setup, find_packages

setup(
    name="pesaflux",
    version="1.0.0",
    author="Your Name",
    author_email="your@email.com",
    description="A modern Python SDK for PesaFlux API (STK Push & Transaction Status).",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pesaflux-sdk",
    packages=find_packages(),
    install_requires=["requests>=2.25.0"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
