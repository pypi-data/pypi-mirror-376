from setuptools import setup, find_packages

# Read README file for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="scalexi_llm",
    version="0.1.1",
    author="scalex_innovation",
    description="A comprehensive multi-provider LLM proxy library with unified interface",
    long_description=long_description,
    long_description_content_type="text/markdown",  # Add your GitHub URL
    packages=find_packages(),
    install_requires=[
        "openai",
        "anthropic",
        "google-genai",
        "groq",
        "pymupdf",
        "xai-sdk",
        "python-docx",
        "pydantic",
        "python-dotenv",
        "exa_py"
    ],
    keywords="llm, ai, openai, anthropic, gemini, groq, deepseek, grok, qwen, exa, proxy, api",
)