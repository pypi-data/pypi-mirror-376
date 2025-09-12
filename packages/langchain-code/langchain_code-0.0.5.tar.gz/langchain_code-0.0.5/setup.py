from pathlib import Path
from setuptools import setup, find_packages

readme = Path("README.md").read_text(encoding="utf-8")

setup(
    name="langchain-code",                 
    version="0.0.1",                       
    description="LangCode – ReAct + Tools + Deep (LangGraph) code agent CLI.",
    long_description=readme,
    long_description_content_type="text/markdown",
    python_requires=">=3.10",
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "click>=8.1.7,<9",
        "typer>=0.12.3",
        "rich==13.7.1",
        "python-dotenv==1.0.1",
        "langchain>=0.2.12",
        "langchain-community>=0.2.10",
        "langchain-anthropic>=0.2.4",
        "langchain-google-genai>=2.0.4",
        "pydantic>=2.7.4,<3",
        "ruamel.yaml==0.18.6",
        "pyfiglet==1.0.4",
        "mcp>=0.4.2",
        "langchain-mcp-adapters>=0.1.7",
        "langchain-tavily>=0.1.0",
        "deepagents>=0.0.3",
        "genai-processors>=1.1.0",
        "langchain-openai>=0.3.0,<0.4.0",
        "langchain-ollama>=0.3.0,<0.4.0",
    ],
    entry_points={
        "console_scripts": [
            "langcode=langchain_code.cli:main",
        ]
    },
    package_data={
        "langchain_code.config": ["mcp.json"]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
)
