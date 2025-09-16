from setuptools import setup, find_packages

setup(
    name="quantumninja-test-package",
    version="0.1.0",
    author="Test User",
    author_email="test@example.com",
    description="A simple test package for PyPI upload",
    long_description="A minimal test package to practice PyPI uploads with twine.",
    long_description_content_type="text/plain",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.6",
)
