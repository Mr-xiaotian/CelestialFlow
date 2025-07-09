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
        "fastapi",
        "uvicorn",           # 作为 FastAPI 的运行服务器
        "redis",
        "pytest",
        "multiprocess",
        "rich",
        "jinja2",            # HTML 模板
    ],
    python_requires=">=3.8",
)
