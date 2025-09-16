from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rnit-vanna",
    version="2.0.0",
    author="RNIT",
    author_email="aryanrathore040@gmail.com",
    description="Enhanced wrapper for Vanna SQL generation library with custom utilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rnit/rnit-vanna",
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

    # MINIMAL CORE - Only 50 packages instead of 110+
    install_requires=[
        "vanna>=0.5.0",  # Core Vanna only (50 packages)
        "python-dotenv>=0.19.0",
    ],

    # OPTIONAL EXTRAS - Let users choose what they need
    extras_require={
        # Most common setup for OpenAI users
        "openai": [
            "openai>=1.0.0",
            "chromadb>=0.4.0",
        ],

        # For Anthropic Claude users
        "anthropic": [
            "anthropic>=0.3.0",
            "chromadb>=0.4.0",
        ],

        # For local LLM users (Ollama, LlamaCpp, etc.)
        "local": [
            "ollama>=0.1.0",
            "chromadb>=0.4.0",
        ],

        # Just vector storage
        "chromadb": [
            "chromadb>=0.4.0",
        ],

        # Database specific
        "postgres": [
            "psycopg2-binary>=2.9.0",
        ],
        "mysql": [
            "pymysql>=1.0.0",
        ],

        # Development tools
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],

        # Everything - for users who want all features
        "all": [
            "openai>=1.0.0",
            "anthropic>=0.3.0",
            "chromadb>=0.4.0",
            "ollama>=0.1.0",
            "psycopg2-binary>=2.9.0",
            "pymysql>=1.0.0",
        ],
    },

    project_urls={
        "Bug Reports": "https://github.com/rnit/rnit-vanna/issues",
        "Source": "https://github.com/rnit/rnit-vanna",
        "Documentation": "https://github.com/rnit/rnit-vanna/wiki",
    },
)