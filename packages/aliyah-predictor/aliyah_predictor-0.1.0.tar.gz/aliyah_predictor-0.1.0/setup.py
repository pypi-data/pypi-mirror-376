from setuptools import setup, find_packages

setup(
    name="aliyah-predictor",  # ✅ Unique name for PyPI
    version="0.1.0",
    description="Empirical and classical linear predictors with agreement metrics",
    long_description_content_type="text/markdown",
    author="Kevin Clarke",
    author_email="your_email@example.com",  # Optional: use a contact email
    url="https://github.com/yourusername/aliyah-predictor",  # Optional: GitHub repo
    packages=find_packages(),
    install_requires=[
        "numpy",
        "scipy"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
