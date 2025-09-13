from setuptools import setup, find_packages

setup(
    name="rnbrw",
    version="0.1.7",   # bump this when you make changes
    author="Behnaz Moradi-Jamei",
    author_email="your_email@domain.com",  # optional but recommended
    description="Renewal Non-Backtracking Random Walk (RNBRW) for scalable community detection",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/lBehnaz-m/RNBRW/",  # can just be placeholder if local
    packages=find_packages(),  # will find rnbrw/ and submodules
    install_requires=[
        "numpy>=1.20",
        "scipy",
        "matplotlib",
        "networkx>=2.6",
        "joblib",
        "python-louvain"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
