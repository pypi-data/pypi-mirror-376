from setuptools import setup, find_packages

setup(
    name="naman_step_sis",  # this is what people will pip install
    version="0.1.0",
    packages=find_packages(),
    description="World's most sus typing effect meme package",
    author="Shreyansh",  # your name
    author_email="SumitLigmaBalls6911@gmail.com",  # can be fake
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
        "Development Status :: 3 - Alpha",
    ],
    python_requires=">=3.7",
)
entry_points={
    "console_scripts": [
        "stepsis=naman_step_sis.typer:type_writer",
    ],
}