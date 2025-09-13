from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
readme = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="bingbong_api",
    version="0.1.0",
    description="A minimal, typed Python client for the BingBong API.",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="you@example.com",
    url="https://example.com/bingbong_api",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.28,<3.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Typing :: Typed",
    ],
    include_package_data=True,
    project_urls={
        "Source": "https://example.com/bingbong_api",
        "Tracker": "https://example.com/bingbong_api/issues",
    },
)
