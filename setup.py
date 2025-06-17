from setuptools import setup, find_packages

setup(
    name="telegram_bot",        # Replace with your actual project name
    version="0.1.0",                 # Or pull from your __init__.py
    author="Nathanmedo_devs",
    author_email="ihemedochinedu@gmail.com",
    description="A telegram bot for cryptocurrency trading and mining",
    packages=find_packages(),        # Automatically finds your Python packages
    install_requires=[],             # Add any dependencies here, e.g. ["requests"]
    python_requires=">=3.8",         # Set your minimum Python version
)
