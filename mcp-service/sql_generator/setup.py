from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sql_generator",
    version="0.1.0",
    author="SQL Generator Team",
    author_email="example@example.com",
    description="A Python library for generating SQL statements based on templates and configurations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/sql_generator",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "jinja2>=3.0.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "postgresql": ["psycopg2-binary>=2.9.0"],
        "mysql": ["pymysql>=1.0.0"],
    },
    include_package_data=True,
    package_data={
        "sql_generator": ["templates/*.sql.j2"],
    },
)
