import os
from setuptools import setup, find_packages

# Read the README.md file
with open(os.path.join(os.path.dirname(__file__), "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="langchain-g4f-chat",
    version="0.1.4",
    description="LangChain integration for g4f",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "langchain-core>=0.1.0",
        "pydantic>=2.0",
        "typing-extensions",
        "requests>=2.25.0",
        "aiohttp>=3.8.0",
        "curl-cffi>=0.5.0",
    ],
    keywords="langchain, gpt4free, g4f, openai, chatgpt, llm",
)