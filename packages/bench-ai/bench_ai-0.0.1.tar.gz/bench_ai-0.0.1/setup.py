from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="bench-ai",
    version="0.0.1",
    author="Raihaan Usman",
    author_email="raihaan@getbench.ai",
    description="🚀 Accelerating engineering workflows at the speed of thought",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://getbench.ai",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Intended Audience :: Manufacturing",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "bench-ai=bench_ai.cli:main",
        ],
    },
    keywords="engineering automation AI workflow CAD CAE optimization",
    project_urls={
        "Homepage": "https://getbench.ai",
        "Source": "https://github.com/bench-tools",
    },
)