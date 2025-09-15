from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")
setup(
    name="mlforgex",
    version="1.0.14",
    packages=find_packages(),
    install_requires = [
    "pandas",
    "numpy",
    "seaborn",
    "matplotlib",
    "scikit-learn",
    "xgboost",
    "imbalanced-learn",
    "tqdm",
    "scipy",
    "requests",
    "nltk",
    "gensim",
    "wordcloud"
]
,
    long_description=long_description,
    long_description_content_type="text/markdown",
    entry_points={
        "console_scripts": [
            "mlforge-train=mlforge.train:main",
            "mlforge-predict=mlforge.predict:main"
        ]
    },
    author="Priyanshu Mathur",
    author_email="mathurpriyanshu2006@gmail.com",
    description="Lightweight ML utility for automated training, evaluation, and prediction with CLI and Python API support",
    license="MIT",
    classifiers=[
         "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    project_urls={
        "Homepage": "https://github.com/dhgefergfefruiwefhjhcduc/ML_Forgex",
        "Documentation": "https://github.com/dhgefergfefruiwefhjhcduc/ML_Forgex/blob/main/README.md",
        "Source": "https://github.com/dhgefergfefruiwefhjhcduc/ML_Forgex",
        "Bug Tracker": "https://github.com/dhgefergfefruiwefhjhcduc/ML_Forgex/issues",
    }
)
