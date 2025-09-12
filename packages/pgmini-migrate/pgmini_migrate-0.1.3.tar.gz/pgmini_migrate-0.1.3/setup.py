from setuptools import setup, find_packages

setup(
    name="pgmini-migrate",
    version="0.1.3",
    packages=find_packages(),
    install_requires=["psycopg2-binary", 'psycopg', 'python-dotenv'],
    entry_points={
        "console_scripts": [
            "pgmigrate=pgmini_migrate.cli:main",
        ],
    },
)
