"""Setup configuration for EAI-CAMP package"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    try:
        with open("README.md", "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return "EAI-CAMP: Enterprise AI Agent Compliance & Audit Management Platform"

# Read requirements
def read_requirements():
    try:
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            return [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return [
            "streamlit>=1.28.0",
            "pandas>=1.5.0",
            "numpy>=1.21.0",
            "plotly>=5.0.0",
            "pyjwt>=2.8.0",
            "bcrypt>=4.0.0",
            "cryptography>=41.0.0",
            "sqlalchemy>=2.0.0",
            "aiohttp>=3.8.0",
            "pydantic>=2.0.0",
            "python-dotenv>=1.0.0",
            "requests>=2.28.0",
        ]

setup(
    name="eai-camp",
    version="0.1.0",
    author="EAI-CAMP Development Team",
    author_email="support@eai-camp.com",
    description="Enterprise AI Agent Compliance & Audit Management Platform",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/eai-camp",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial",
        "Topic :: Security",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
