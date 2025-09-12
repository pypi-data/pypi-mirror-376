from setuptools import setup, find_packages

setup(
    name="lazyslurm",
    version="0.1.0",
    author="Mateus Figueiredo",
    author_email="mtsodf@gmail.com",
    description="A interface for SLURM job management.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/mtsodf/lazyslurm",
    packages=find_packages(),
    install_requires=["urwid", "plumbum"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "lazyslurm = lazyslurm.main:main",
        ]
    },
)
