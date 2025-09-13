from setuptools import setup, find_packages

setup(
    name="scalexi_llm",
    version="0.1.0",
    author="scalex_innovation",
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
)