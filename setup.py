from setuptools import setup, find_packages

setup(
    name="CelestialFlow",
    version="3.0.1",
    description="A DAG-based multiprocessing task framework",
    author="Mr-xiaotian",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    install_requires=[
        "tqdm",
        "loguru",
        "fastapi",
        "uvicorn",
        "requests",
        "networkx",
        "redis",
        "httpx",
        "jinja2",
    ],
    python_requires=">=3.8",
)
