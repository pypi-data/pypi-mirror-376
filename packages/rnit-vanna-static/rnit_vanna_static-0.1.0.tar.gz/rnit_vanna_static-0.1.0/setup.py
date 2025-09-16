from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rnit-vanna-static",
    version="0.1.0",
    author="RNIT",
    author_email="aryanrathore040@gmail.com",
    description="Static snapshot of Vanna SQL generation library (for testing/offline use)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rnit/rnit-vanna-static",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
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
    keywords="sql nlp gpt openai database query natural-language",
    python_requires=">=3.7",
    install_requires=[
        "openai>=1.0.0",
        "chromadb>=0.4.0",
        "flask>=2.0.0",
        "flask-cors>=3.0.0",
        "pandas>=1.3.0",
        "sqlalchemy>=1.4.0",
        "plotly>=5.0.0",
        "kaleido>=0.2.0",
        "python-dotenv>=0.19.0",
    ],
)