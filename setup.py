from setuptools import setup, find_packages

setup(
    name="CelestialFlow",
    version="0.1.0",
    description="A DAG-based multiprocessing task framework",
    author="Xiaotian",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    install_requires=[
        "flask",
        "redis",
        "pytest",
        "multiprocess",
        "rich",
        # 其他依赖...
    ],
    python_requires=">=3.8",
)
