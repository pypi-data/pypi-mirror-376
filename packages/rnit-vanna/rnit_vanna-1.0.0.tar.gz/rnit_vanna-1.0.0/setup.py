from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rnit-vanna",
    version="1.0.0",
    author="RNIT",
    author_email="your-email@example.com",
    description="Enhanced wrapper for Vanna SQL generation library with custom utilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/rnit-vanna",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Database",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords="sql nlp gpt openai database query natural-language vanna ai",
    python_requires=">=3.7",
    install_requires=[
        "vanna[chromadb,openai]>=0.5.0",  # Always uses latest Vanna!
        "python-dotenv>=0.19.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],
        "postgres": [
            "psycopg2-binary>=2.9.0",
        ],
        "mysql": [
            "pymysql>=1.0.0",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/rnit-vanna/issues",
        "Source": "https://github.com/yourusername/rnit-vanna",
        "Documentation": "https://github.com/yourusername/rnit-vanna/wiki",
    },
)