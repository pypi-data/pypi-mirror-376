from setuptools import find_packages, setup

setup(
    name="vivi_analytics_library",
    version="2.1.1",
    author="Developer",
    description="A library with methods used in data pipelines for analytics and reports.",
    packages=find_packages(),
    install_requires=[
        "aiohttp",
        "pydantic",
        "openai==1.99.6",
    ],
    python_requires=">=3.10",
)
