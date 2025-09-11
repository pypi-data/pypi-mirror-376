from setuptools import setup, find_packages

setup(
    name="aem-page-verifier",  # Unique name for PyPI (check availability)
    version="0.1.1",  # Initial version
    author="Your Name",  # Replace with your name
    author_email="your.email@example.com",  # Replace with your email
    description="A tool to compare AEM publish pages with the author server",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/aem-page-verifier",  # Replace with your repo (optional)
    packages=find_packages(),  # Automatically finds aem_page_verifier/
    install_requires=[
        "requests>=2.32.3",
    ],
    entry_points={
        "console_scripts": [
            "aem-verify=aem_page_verifier.verifier:main"  # CLI command
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)