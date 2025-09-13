from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

setup(
    name="manufacturing-forecast",
    version="0.2.0",
    author="Manufacturing Forecast Team",
    author_email="contact@example.com",
    description="A Python package for machine learning and data processing methods for manufacturing forecasting",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/manufacturing_forecast",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black",
            "isort",
            "flake8",
            "mypy",
        ],
        "catboost": ["catboost>=1.0"],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/manufacturing_forecast/issues",
        "Source": "https://github.com/yourusername/manufacturing_forecast",
    },
)
