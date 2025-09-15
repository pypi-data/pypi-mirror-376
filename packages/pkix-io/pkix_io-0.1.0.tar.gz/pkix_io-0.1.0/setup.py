"""
PKIX Python Package Setup
Package name reservation for PyPI
"""

from setuptools import setup, find_packages

# Read README file
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "PKIX Certificate Lifecycle Management Platform - Package Reserved"

setup(
    name="pkix-io",
    version="0.1.0",
    author="Evan Nevermore",
    author_email="pkix-pypi@pkix.io",
    description="PKIX Certificate Lifecycle Management Platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pkix-io/pkix",
    project_urls={
        "Homepage": "https://pkix.io",
        "Documentation": "https://docs.pkix.io",
        "Source": "https://github.com/pkix-io/pkix",
        "Tracker": "https://github.com/pkix-io/pkix/issues",
    },
    packages=find_packages(),
    classifiers=[
        # Development Status
        "Development Status :: 2 - Pre-Alpha",

        # Intended Audience
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",

        # Topic
        "Topic :: Security :: Cryptography",
        "Topic :: System :: Systems Administration",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Software Development :: Libraries :: Python Modules",

        # Environment
        "Environment :: Web Environment",
        "Environment :: Console",

        # Operating System
        "Operating System :: OS Independent",

        # Python Versions
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
    ],
    keywords=[
        "pkix",
        "pki",
        "certificates",
        "x509",
        "certificate-management",
        "lifecycle-management",
        "tls",
        "ssl",
        "ca",
        "certificate-authority",
        "acme",
        "letsencrypt"
    ],
    python_requires=">=3.8",
    install_requires=[
        # Minimal dependencies for reservation package
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pkix-io=pkix_io.cli:main",
        ],
    },
    package_data={
        "pkix": ["py.typed"],
    },
    include_package_data=True,
    zip_safe=False,
)