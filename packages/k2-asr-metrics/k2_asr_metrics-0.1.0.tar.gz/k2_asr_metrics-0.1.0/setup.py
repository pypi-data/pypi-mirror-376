from setuptools import setup, find_packages

setup(
    name="k2_asr_metrics",
    version="0.1.0",
    description="Custom ASR evaluation metrics (token accuracy, sentence accuracy, precision, recall, F1, char accuracy, edit distance)",
    author="Krishna Kumar Singh",
    packages=find_packages(),
    install_requires=[
        "scikit-learn",
        "editdistance"
    ],
    python_requires=">=3.10",
)
