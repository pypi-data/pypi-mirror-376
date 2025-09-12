from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="bench-sdk",
    version="0.0.1",
    author="Raihaan Usman",
    author_email="raihaan@getbench.ai",
    description="🛠️ The SDK for building AI-powered engineering automation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://getbench.ai",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Intended Audience :: Manufacturing",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "bench-sdk=bench_sdk.cli:main",
        ],
    },
    keywords="SDK engineering automation AI API framework CAD CAE workflow",
    project_urls={
        "Homepage": "https://getbench.ai",
        "Source": "https://github.com/bench-tools",
        "Documentation": "https://docs.getbench.ai",
    },
)