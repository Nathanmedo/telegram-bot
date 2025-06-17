from setuptools import setup, find_packages

setup(
    name="your_project_name",        # Replace with your actual project name
    version="0.1.0",                 # Or pull from your __init__.py
    author="Your Name",
    author_email="you@example.com",
    description="A short description of your project",
    packages=find_packages(),        # Automatically finds your Python packages
    install_requires=[],             # Add any dependencies here, e.g. ["requests"]
    python_requires=">=3.8",         # Set your minimum Python version
)
