import os.path
from setuptools import find_packages, setup

HERE = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(HERE, "README.md")) as fid:
    README = fid.read()

setup(
    name="alignmeet",
    version="1.0.4",
    description="A Comprehensive Tool for Meeting Alignment, Annotation and Evaluation",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/ELITR/alignmeet",
    author="Peter Polak",
    author_email="polak@ufal.mff.cuni.cz",
    license="TBD",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "numpy", "PySide2", "python-vlc"
    ],
    entry_points={"console_scripts": ["alignmeet=alignmeet.__main__:main"]},
)
