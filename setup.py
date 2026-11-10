from setuptools import setup, find_packages

setup(
    name="blocktrace-ai",
    version="1.0.0",
    description="Offline Bitcoin forensic analysis correlating blockchain records with network logs using Graph Analysis and Explainable AI",
    author="Tech Titans (Ramit Layek, Nikhil Sharma, Mayank Sharma)",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "streamlit>=1.30.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
        "networkx>=3.0",
        "pyvis>=0.3.2",
        "plotly>=5.18.0",
        "shap>=0.44.0",
        "matplotlib>=3.8.0",
    ],
    entry_points={
        "console_scripts": [
            "blocktrace=blocktrace.cli:main",
        ],
    },
)
